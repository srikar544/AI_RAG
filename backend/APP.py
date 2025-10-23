"""
app.py
-------

This module serves as the main web entry point for the RAG (Retrieval-Augmented Generation) pipeline.

Responsibilities:
1. Accept user questions and enqueue them into RabbitMQ.
2. Listen for processed answers published back via Redis Pub/Sub.
3. Broadcast results to all connected WebSocket clients in real time.
4. Serve a simple frontend (if any) via Flask.

Tech stack:
- Flask (REST API)
- Flask-SocketIO (real-time communication)
- Redis (Pub/Sub channel for RAG results)
- RabbitMQ (task queue between API and worker)
"""

import threading
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import redis

# Local imports
from producer import send_task                     # Pushes user questions into RabbitMQ
from db_setup import SessionLocal, QueryResult      # ORM models and DB session
from config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    REDIS_RESULTS_CHANNEL, RABBITMQ_QUEUE, RABBITMQ_HOST
)

# -----------------------------------------------------------------------------
# Flask + SocketIO Setup
# -----------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="frontend/static",  # static files folder
    template_folder="frontend"        # HTML templates folder
)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
# -----------------------------------------------------------------------------
# Redis Setup
# -----------------------------------------------------------------------------
# Redis client — used to subscribe to a channel where worker publishes results
_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


# -----------------------------------------------------------------------------
# Redis Subscriber Thread
# -----------------------------------------------------------------------------
def redis_subscriber():
    """
    Continuously listens to the Redis Pub/Sub channel (REDIS_RESULTS_CHANNEL)
    for new RAG results published by the worker.

    When a new message arrives:
    - Parse the JSON message.
    - Broadcast it to all connected WebSocket clients via SocketIO.
    """
    pubsub = _r.pubsub()
    pubsub.subscribe(REDIS_RESULTS_CHANNEL)
    print("[app] Redis subscriber started, listening for results...")

    # Blocking loop that listens indefinitely
    for message in pubsub.listen():
        # Each message is a dict with keys like {'type': 'message', 'data': '...'}
        if message and message.get("type") == "message":
            try:
                # Parse JSON payload received from worker
                data = json.loads(message.get("data"))

                # Emit to all connected WebSocket clients in real time
                socketio.emit("rag_result", data)
            except Exception as e:
                print("[app] Error parsing message:", e)


# -----------------------------------------------------------------------------
# WebSocket Events
# -----------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    """
    Triggered automatically when a WebSocket client connects.

    Sends a small acknowledgment message so the frontend
    knows the connection is established.
    """
    emit("server_message", {"message": "Connected to RAG WebSocket"})


# -----------------------------------------------------------------------------
# HTTP Routes
# -----------------------------------------------------------------------------
@app.route("/")
def serve_frontend():
    """
    Serves the main frontend page (index.html) from the /frontend directory.
    Useful if your frontend (React, Vue, etc.) is bundled into this folder.
    """
    return send_from_directory("frontend", "index.html")


@app.route("/ask", methods=["POST"])
def ask():
    """
    Endpoint: /ask
    Method: POST

    Description:
    Accepts a user question along with one or more PDF IDs, 
    and queues tasks for processing by the RAG worker.
    Each PDF will be processed independently.

    Request JSON Example:
    {
        "user": "Alice",               # optional, defaults to "web_user"
        "question": "What is RAG?",    # required
        "pdf_ids": ["doc1.pdf", "doc2.pdf"]  # optional, defaults to ["default.pdf"]
    }

    Response JSON Example:
    {
        "status": "queued",
        "pdfs": ["doc1.pdf", "doc2.pdf"]
    }

    Flow:
    1. Parse JSON payload.
    2. Validate that 'question' exists.
    3. Extract 'user' and 'pdf_ids'.
    4. Queue a separate task for each PDF using RabbitMQ.
    5. Respond with confirmation JSON.
    """

    # 1. Parse JSON payload
    payload = request.get_json()

    # 2. Extract user (defaults to "web_user")
    user = payload.get("user", "web_user")

    # 3. Validate question field
    question = payload.get("question")
    if not question:
        return jsonify({"error": "question required"}), 400

    # 4. Extract list of PDF IDs (defaults to ["default.pdf"])
    pdf_ids = payload.get("pdf_ids", ["default.pdf"])

    # 5. For each PDF, enqueue a task in RabbitMQ
    for pdf_id in pdf_ids:
        send_task(user, question, pdf_id)

    # 6. Return confirmation
    return jsonify({"status": "queued", "pdfs": pdf_ids})


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    When run directly (python app.py):
    1. Start a background thread that listens for results on Redis.
    2. Launch Flask-SocketIO web server for API + WebSocket handling.
    """
    # Start Redis subscriber as a daemon thread
    t = threading.Thread(target=redis_subscriber, daemon=True)
    t.start()

    # Start Flask-SocketIO server
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

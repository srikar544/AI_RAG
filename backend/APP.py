"""
app.py
-------

Main web entry point for the RAG (Retrieval-Augmented Generation) pipeline.

Responsibilities:
1. Accept user questions and enqueue them into RabbitMQ.
2. Listen for processed answers published via Redis Pub/Sub.
3. Broadcast results to connected WebSocket clients in real time.
4. Serve a frontend via Flask templates and static files.

Tech stack:
- Flask (REST API)
- Flask-SocketIO (real-time communication)
- Redis (Pub/Sub channel for RAG results)
- RabbitMQ (task queue)
"""

import threading
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import redis

# Local imports
from producer import send_task                     # Pushes user questions into RabbitMQ
from db_setup import SessionLocal, QueryResult    # ORM models and DB session
from config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    REDIS_RESULTS_CHANNEL, RABBITMQ_QUEUE, RABBITMQ_HOST
)

# --------------------------------------------------------------------------
# Flask + SocketIO Setup
# --------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="frontend/static",    # CSS/JS/images
    template_folder="frontend/templates"  # HTML templates
)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --------------------------------------------------------------------------
# Redis Setup
# --------------------------------------------------------------------------
_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# --------------------------------------------------------------------------
# Redis Subscriber Thread
# --------------------------------------------------------------------------
def redis_subscriber():
    """Listen to Redis channel and emit RAG results via WebSocket."""
    pubsub = _r.pubsub()
    pubsub.subscribe(REDIS_RESULTS_CHANNEL)
    print("[app] Redis subscriber started, listening for results...")

    for message in pubsub.listen():
        if message and message.get("type") == "message":
            try:
                data = json.loads(message.get("data"))
                socketio.emit("rag_result", data)
            except Exception as e:
                print("[app] Error parsing message:", e)

# --------------------------------------------------------------------------
# WebSocket Events
# --------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    emit("server_message", {"message": "Connected to RAG WebSocket"})

# --------------------------------------------------------------------------
# HTTP Routes
# --------------------------------------------------------------------------
@app.route("/")
def serve_frontend():
    """Serve index.html from templates folder."""
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    """Accept a question + PDF IDs and queue tasks for processing."""
    payload = request.get_json()
    user = payload.get("user", "web_user")
    question = payload.get("question")
    if not question:
        return jsonify({"error": "question required"}), 400
    pdf_ids = payload.get("pdf_ids", ["default.pdf"])

    for pdf_id in pdf_ids:
        send_task(user, question, pdf_id)

    return jsonify({"status": "queued", "pdfs": pdf_ids})

# --------------------------------------------------------------------------
# Entry Point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # Start Redis subscriber thread
    t = threading.Thread(target=redis_subscriber, daemon=True)
    t.start()

    # Run Flask-SocketIO server
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

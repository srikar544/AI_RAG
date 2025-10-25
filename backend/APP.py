"""
app.py
-------

Main web entry point for the RAG (Retrieval-Augmented Generation) pipeline.

Responsibilities:
1. Accept user questions and enqueue them into RabbitMQ.
2. Listen for processed answers published via Redis Pub/Sub.
3. Broadcast results to connected WebSocket clients in real time.
4. Serve frontend templates and static files.

Tech stack:
- Flask (REST API)
- Flask-SocketIO (real-time communication)
- Redis (Pub/Sub channel for RAG results)
- RabbitMQ (task queue)
"""

import threading
import json
import os
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import redis

# Project modules
from producer import send_task
from db_setup import SessionLocal, QueryResult
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_RESULTS_CHANNEL

PDF_FOLDER = r"D:\srikardata\AI\AI_RAG\backend\pdfs"



# -----------------------------
# Flask + SocketIO Setup
# -----------------------------
app = Flask(
    __name__,
    static_folder="frontend/static",     # CSS/JS/images
    template_folder="frontend/templates" # HTML templates
)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# -----------------------------
# Redis Setup
# -----------------------------
_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# -----------------------------
# Redis Subscriber Thread
# -----------------------------
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

# -----------------------------
# WebSocket Events
# -----------------------------
@socketio.on("connect")
def handle_connect():
    emit("server_message", {"message": "Connected to RAG WebSocket"})

# -----------------------------
# HTTP Routes
# -----------------------------
@app.route("/")
def serve_frontend():
    """Serve main frontend page."""
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    """Accept a question + PDF IDs and queue tasks for processing."""
    payload = request.get_json()
    user = payload.get("user", "web_user")
    question = payload.get("question")
    if not question:
        return jsonify({"error": "question required"}), 400

    pdf_ids = payload.get("pdf_ids", [])
    # Keep only existing PDFs
    pdf_ids = [pdf for pdf in pdf_ids if os.path.exists(os.path.join(PDF_FOLDER, pdf))]
    if not pdf_ids:
        return jsonify({"status": "error", "message": "No valid PDFs selected"}), 400

    for pdf_id in pdf_ids:
        send_task(user, question, pdf_id)

    return jsonify({"status": "queued", "pdfs": pdf_ids})


@app.route("/recent", methods=["GET"])
def recent():
    """Return recent question-answer history from database."""
    session = SessionLocal()
    results = session.query(QueryResult).order_by(QueryResult.timestamp.desc()).limit(10).all()
    out = []
    for r in results:
        out.append({
            "user": r.user,
            "question": r.question,
            "answer": r.answer,
            "llm_model": r.llm_model,
            "cache_hit": r.cache_hit
        })
    session.close()
    return jsonify(out)

@app.route("/pdf_list", methods=["GET"])
def pdf_list():
    """Return list of PDF files available in PDF_FOLDER."""
    try:
        files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Main Entry
# -----------------------------
if __name__ == "__main__":
    # Start Redis subscriber thread
    t = threading.Thread(target=redis_subscriber, daemon=True)
    t.start()

    # Run Flask-SocketIO server
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

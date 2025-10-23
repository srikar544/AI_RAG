# app.py
import threading
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import redis

# Local imports
from producer import send_task
from db_setup import SessionLocal, QueryResult
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_RESULTS_CHANNEL

# ------------------- Flask + SocketIO Setup -------------------
app = Flask(
    __name__,
    static_folder="frontend/static",  # static files folder
    template_folder="frontend"        # HTML templates folder
)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ------------------- Redis Setup -------------------
_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def redis_subscriber():
    """Listen to Redis channel for RAG results and broadcast via WebSocket"""
    pubsub = _r.pubsub()
    pubsub.subscribe(REDIS_RESULTS_CHANNEL)
    print("[app] Redis subscriber started...")
    for message in pubsub.listen():
        if message and message.get("type") == "message":
            try:
                data = json.loads(message.get("data"))
                socketio.emit("rag_result", data)
            except Exception as e:
                print("[app] Error parsing Redis message:", e)

# ------------------- WebSocket Events -------------------
@socketio.on("connect")
def handle_connect():
    emit("server_message", {"message": "Connected to RAG WebSocket"})

# ------------------- HTTP Routes -------------------
@app.route("/")
def index():
    """Serve the main HTML page"""
    return send_from_directory("frontend", "index.html")

@app.route("/ask", methods=["POST"])
def ask():
    """Queue user question to RabbitMQ"""
    payload = request.get_json()
    user = payload.get("user", "web_user")
    question = payload.get("question")
    if not question:
        return jsonify({"error": "question required"}), 400
    pdf_ids = payload.get("pdf_ids", ["default.pdf"])
    for pdf_id in pdf_ids:
        send_task(user, question, pdf_id)
    return jsonify({"status": "queued", "pdfs": pdf_ids})

# Optional: explicit static route if needed
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("frontend/static", filename)

@app.route("/recent")
def recent():
    session = SessionLocal()
    results = session.query(QueryResult).order_by(QueryResult.created_at.desc()).limit(10).all()
    session.close()
    return jsonify([
        {
            "user": r.user,
            "question": r.question,
            "answer": r.answer,
            "llm_model": r.llm_model,
            "cache_hit": r.cache_hit
        } for r in results
    ])

# ------------------- Entry Point -------------------
if __name__ == "__main__":
    # Start Redis subscriber in a background thread
    threading.Thread(target=redis_subscriber, daemon=True).start()
    # Run Flask-SocketIO server
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

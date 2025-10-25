# Intelligent RAG Pipeline (RabbitMQ + Redis + WebSocket)

## Overview
This project is an end-to-end Retrieval-Augmented Generation (RAG) system with:

- **Asynchronous query processing** via RabbitMQ
- **Redis caching** and **WebSocket result streaming**
- **SQLite database** for storing user queries and results
- **Flask + Flask-SocketIO frontend** for live updates
- **Dynamic prompt generation and metadata extraction** (lightweight NLP)
- **Mock RAG engine** (replaceable with FAISS / LangChain + LLMs)

The architecture supports multiple users and questions simultaneously, with caching and batching to improve throughput.

---

## Project Structure


rag_project/
│
├── app.py # Flask API + WebSocket server
├── producer.py # Send questions to RabbitMQ
├── consumer.py # Worker that processes questions
├── config.py # Configs: Redis, RabbitMQ, DB, batching
├── db_setup.py # SQLite DB models
├── rag_engine.py # Core RAG engine (mock or real)
├── rag_pipeline.py # Metadata + dynamic prompt + model selection
├── cache_manager.py # Redis caching & pub/sub
├── monitor.py # Optional: queue monitoring
├── requirements.txt
├── README.md
└── frontend/
├── index.html
├── app.js
└── style.css


---

## Prerequisites

- Python 3.9+
- RabbitMQ
- Redis
- (Optional) SQLite comes with Python standard library

### Install RabbitMQ & Redis

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install rabbitmq-server redis-server
sudo systemctl enable --now rabbitmq-server
sudo systemctl enable --now redis-server

pip install -r requirements.txt

Flask>=2.0
flask-socketio>=5.0
python-socketio>=5.0
pika>=1.2.0
redis>=4.0
SQLAlchemy>=1.4
requests


how to run

python app.py

Runs at http://localhost:5000/
Handles /ask endpoint and WebSocket connections
Streams live RAG results to connected clients

python consumer.py


Listens to RabbitMQ queue
Checks Redis cache
Calls rag_pipeline.py → rag_engine.py
Stores results in DB and publishes via Redis channel

python producer.py

curl -X POST http://localhost:5000/ask \
     -H "Content-Type: application/json" \
     -d '{"user":"Alice","question":"Summarize the introduction.","pdf_id":"sample.pdf"}'


open frontend

Navigate to http://localhost:5000/ in your browser
Enter your name and question
Watch live results appear as answers are generated
Refresh Recent DB section to see past queries

python monitor.py

| Feature             | Implementation                                                       |
| ------------------- | -------------------------------------------------------------------- |
| Dynamic prompt      | `rag_pipeline.py` builds instruction with metadata                   |
| Metadata extraction | Extracts intent, keywords, and length from question                  |
| Model selection     | `select_model()` chooses GPT-3.5 / GPT-4 based on heuristics         |
| RAG engine          | `rag_engine.py` handles embeddings, retrieval, and answer generation |
| Caching             | Redis cache with TTL, prevents repeated computation                  |
| Live streaming      | Flask-SocketIO + Redis pub/sub                                       |


FLOW

Flow of Asking Questions to PDFs
Frontend (index.html + app.js)
User enters their name, PDF ID, and question in the browser.
Presses Submit → triggers an HTTP POST request to Flask or emits a WebSocket event.
Flask API / WebSocket server (app.py)
Receives the question and user info.
Publishes the question to RabbitMQ queue using producer.py logic.
If using WebSocket, the connection is kept open for streaming results.
RabbitMQ Queue
Holds all incoming questions asynchronously.
Multiple questions from multiple users can queue up.
Consumer Worker (consumer.py)
Listens to RabbitMQ.
For each question:
Checks Redis cache: if the same question was already answered, it uses cached result.
Calls rag_pipeline.py → rag_engine.py:
Loads the PDF (or retrieves vector embeddings)
Runs retrieval + generation to produce the answer.
Stores the answer in SQLite DB.
Publishes the answer back via WebSocket (or Redis pub/sub).
Frontend (app.js)
Listens for WebSocket events.
As soon as the answer is available, it is displayed live in the browser.
User sees the answer appear in real-time without refreshing.


docker run -d --name my-redis -p 6379:6379 redis
docker run -d --name my-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

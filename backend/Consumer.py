"""
consumer.py
------------
RabbitMQ consumer for RAG pipeline.
"""

import sys
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import pika

# -----------------------------
# Add utils folder to path
# -----------------------------
utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
sys.path.append(utils_path)

# -----------------------------
# Local imports (project modules)
# -----------------------------
from config import (
    RABBITMQ_HOST,
    RABBITMQ_QUEUE,
    PREFETCH_COUNT,
    BATCH_SIZE,
    WORKER_THREAD_POOL,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD
)
from cache_manager import get_cached_answer, set_cached_answer, publish_result
from rag_pipeline import run_pipeline
from db_setup import SessionLocal, QueryResult

# -----------------------------
# Thread pool and batch buffer
# -----------------------------
executor = ThreadPoolExecutor(max_workers=WORKER_THREAD_POOL)
batch_buffer = []
buffer_lock = threading.Lock()

# -----------------------------
# Database helper
# -----------------------------
def save_result_db(user, question, answer, llm_model, metadata, cache_hit=False):
    session = SessionLocal()
    qr = QueryResult(
        user=user,
        question=question,
        answer=answer,
        llm_model=llm_model,
        cache_hit=cache_hit,
        metadata=json.dumps(metadata) if metadata else None
    )
    session.add(qr)
    session.commit()
    session.close()

# -----------------------------
# Task processor
# -----------------------------
def process_single_item(item):
    user = item.get("user", "anonymous")
    question = item.get("question", "")
    pdf_ids = item.get("pdf_ids") or [item.get("pdf_id", "default.pdf")]

    for pdf_id in pdf_ids:
        cached = get_cached_answer(question, pdf_id)
        if cached:
            save_result_db(user, question, cached, "CACHE", {"cached": True}, cache_hit=True)
            publish_result({
                "user": user,
                "question": question,
                "pdf_id": pdf_id,
                "answer": cached,
                "llm_model": "CACHE"
            })
            continue

        result = run_pipeline(question, pdf_id)
        answer = result["answer"]
        metadata = result["metadata"]
        llm_model = result["llm_model"]

        save_result_db(user, question, answer, llm_model, metadata, cache_hit=False)
        set_cached_answer(question, pdf_id, answer, metadata)
        publish_result({
            "user": user,
            "question": question,
            "pdf_id": pdf_id,
            "answer": answer,
            "llm_model": llm_model
        })

# -----------------------------
# Batch processor
# -----------------------------
def process_batch(batch):
    for item in batch:
        executor.submit(process_single_item, item)

# -----------------------------
# RabbitMQ callback
# -----------------------------
def on_message(ch, method, properties, body):
    global batch_buffer
    try:
        data = json.loads(body)
    except Exception:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    with buffer_lock:
        batch_buffer.append(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if len(batch_buffer) >= BATCH_SIZE:
            to_process = batch_buffer[:]
            batch_buffer = []
            threading.Thread(target=process_batch, args=(to_process,)).start()

# -----------------------------
# Run consumer
# -----------------------------
def run_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    ch = conn.channel()
    ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    ch.basic_qos(prefetch_count=PREFETCH_COUNT)
    ch.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=on_message)

    print("[consumer] Waiting for messages...")
    ch.start_consuming()

# -----------------------------
# Script entry
# -----------------------------
if __name__ == "__main__":
    run_consumer()

"""
consumer.py
------------

Purpose:
    This module consumes tasks (questions) from RabbitMQ, processes them through
    the RAG pipeline, caches and saves results, and publishes the final answers
    back to Redis for the frontend to consume in real-time.

Core Responsibilities:
    1. Continuously listen for tasks from RabbitMQ.
    2. For each task:
        - Check if the answer already exists in Redis cache.
        - If cached → publish instantly and mark cache_hit=True.
        - If not cached → run the RAG pipeline (vector retrieval + LLM).
    3. Save all answers into the database (via SQLAlchemy).
    4. Publish final results to Redis Pub/Sub channel.
    5. Use ThreadPoolExecutor to process tasks concurrently.

Main Components:
    - RabbitMQ → message queue (input)
    - Redis → cache + pub/sub for results (output)
    - Database → persistence of question-answer history
    - ThreadPool → concurrent worker execution
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
import pika
import sys
import os

# Add the utils folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))

# Local imports (project modules)
from config import (
    RABBITMQ_HOST,
    RABBITMQ_QUEUE,
    PREFETCH_COUNT,
    BATCH_SIZE,
    WORKER_THREAD_POOL
)
from cache_manager import get_cached_answer, set_cached_answer, publish_result
from rag_pipeline import run_pipeline
from db_setup import SessionLocal, QueryResult

# -----------------------------------------------------------------------------
# Global thread pool and buffers
# -----------------------------------------------------------------------------
# Used to parallelize RAG processing so multiple tasks can run concurrently.
executor = ThreadPoolExecutor(max_workers=WORKER_THREAD_POOL)

# Temporary buffer to collect messages into small batches
batch_buffer = []
buffer_lock = threading.Lock()


# -----------------------------------------------------------------------------
# Database Persistence Helper
# -----------------------------------------------------------------------------
def save_result_db(user, question, answer, llm_model, metadata, cache_hit=False):
    """
    Save a single question-answer record to the database.

    Args:
        user (str): Username or request origin identifier.
        question (str): The input question.
        answer (str): The LLM-generated or cached answer.
        llm_model (str): The name of the model used (e.g. GPT-4, Mistral, CACHE).
        metadata (dict): Additional details from the RAG pipeline.
        cache_hit (bool): Indicates if the result came from cache.
    """
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


# -----------------------------------------------------------------------------
# Task Processor
# -----------------------------------------------------------------------------
def process_single_item(item):
    """
    Process a single queued item from RabbitMQ.

    Flow:
        1. Extract user, question, and PDF(s).
        2. Check Redis cache to see if the answer already exists.
        3. If cached → publish cached answer immediately.
        4. If not cached → call the RAG pipeline (retrieval + LLM inference).
        5. Save answer to DB, update cache, and publish to Redis.

    Args:
        item (dict): JSON task containing user, question, and pdf_ids.
    """
    user = item.get("user", "anonymous")
    question = item.get("question", "")

    # Support both single or multiple PDFs
    pdf_ids = item.get("pdf_ids") or [item.get("pdf_id", "default.pdf")]

    for pdf_id in pdf_ids:
        # Step 1: Check Redis cache first
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
            continue  # Skip reprocessing

        # Step 2: Run the actual RAG pipeline
        result = run_pipeline(question, pdf_id)
        answer = result["answer"]
        metadata = result["metadata"]
        llm_model = result["llm_model"]

        # Step 3: Save to DB + update cache + publish to Redis
        save_result_db(user, question, answer, llm_model, metadata, cache_hit=False)
        set_cached_answer(question, pdf_id, answer, metadata)
        publish_result({
            "user": user,
            "question": question,
            "pdf_id": pdf_id,
            "answer": answer,
            "llm_model": llm_model
        })


# -----------------------------------------------------------------------------
# Batch Processor
# -----------------------------------------------------------------------------
def process_batch(batch):
    """
    Process a small batch of tasks concurrently.

    Args:
        batch (list): A list of task dictionaries from RabbitMQ.

    Note:
        Each task in the batch is submitted to the ThreadPoolExecutor.
        This improves throughput for high-traffic systems.
    """
    for item in batch:
        executor.submit(process_single_item, item)


# -----------------------------------------------------------------------------
# RabbitMQ Consumer Callback
# -----------------------------------------------------------------------------
def on_message(ch, method, properties, body):
    """
    RabbitMQ callback function.
    Triggered automatically when a new message is received from the queue.

    Responsibilities:
        - Parse the message payload (JSON).
        - Add it to a temporary batch buffer.
        - Acknowledge (ack) the message immediately.
        - When batch size is reached → spawn a thread to process the batch.

    Args:
        ch: Channel object from pika.
        method: Delivery metadata.
        properties: Message properties.
        body (bytes): Raw message payload from RabbitMQ.
    """
    global batch_buffer
    try:
        data = json.loads(body)
    except Exception:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Add message to batch buffer safely
    with buffer_lock:
        batch_buffer.append(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # acknowledge immediately

        # If buffer is full, process the batch asynchronously
        if len(batch_buffer) >= BATCH_SIZE:
            to_process = batch_buffer[:]
            batch_buffer = []
            threading.Thread(target=process_batch, args=(to_process,)).start()


# -----------------------------------------------------------------------------
# Consumer Entry Point
# -----------------------------------------------------------------------------
def run_consumer():
    """
    Initializes RabbitMQ connection and begins consuming messages.

    Steps:
        1. Connect to RabbitMQ host.
        2. Declare the queue (durable so messages survive restarts).
        3. Set prefetch_count for fair dispatch (limits unacknowledged messages).
        4. Start consuming messages using on_message() callback.
    """
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    ch = conn.channel()
    ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    ch.basic_qos(prefetch_count=PREFETCH_COUNT)
    ch.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=on_message)

    print("[consumer] Waiting for messages...")
    ch.start_consuming()


# -----------------------------------------------------------------------------
# Script Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    If executed directly:
    - Launch the RabbitMQ consumer loop.
    - This worker runs indefinitely, pulling tasks from the queue and processing them.
    """
    run_consumer()

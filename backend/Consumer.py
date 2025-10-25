"""
consumer.py
------------
Minimal RabbitMQ consumer for testing RAG pipeline locally.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import pika

from rag_pipeline import run_pipeline

# -----------------------------
# Setup logging
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -----------------------------
# RabbitMQ Configuration
# -----------------------------
RABBITMQ_HOST = "localhost"
RABBITMQ_QUEUE = "rag_queue"
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"
PREFETCH_COUNT = 1
BATCH_SIZE = 1  # Set to 1 for immediate processing
WORKER_THREAD_POOL = 2

# -----------------------------
# Thread pool & buffer
# -----------------------------
executor = ThreadPoolExecutor(max_workers=WORKER_THREAD_POOL)
batch_buffer = []
buffer_lock = threading.Lock()

# -----------------------------
# Simulated RAG pipeline function
# -----------------------------
#def run_pipeline(question, pdf_id):
#    answer = f"Simulated answer for '{question}' using '{pdf_id}'"
#    metadata = {"source": pdf_id}
#    llm_model = "SIMULATED_MODEL"
#    return {"answer": answer, "metadata": metadata, "llm_model": llm_model}

# -----------------------------
# Print / log result
# -----------------------------
def publish_result(result):
    logging.info(f"[RESULT] {result['answer']} (User: {result['user']}, PDF: {result['pdf_id']})")
    print(f"[ANSWER] {result['question']} -> {result['answer']}")

# -----------------------------
# Process a single task
# -----------------------------
def process_single_item(item):
    # Ensure item is a dict
    if isinstance(item, str):
        try:
            item = json.loads(item)
        except json.JSONDecodeError:
            logging.error(f"[consumer] Invalid JSON: {item}")
            return

    user = item.get("user", "anonymous")
    question = item.get("question", "")
    pdf_ids = item.get("pdf_ids") or [item.get("pdf_id", "default.pdf")]

    for pdf_id in pdf_ids:
        result = run_pipeline(question, pdf_id)
        answer = result["answer"]
        metadata = result["metadata"]
        llm_model = result["llm_model"]

        publish_result({
            "user": user,
            "question": question,
            "pdf_id": pdf_id,
            "answer": answer,
            "llm_model": llm_model
        })
        print(f"[ANSWER] {question} -> {answer}")
# -----------------------------
# Batch processor (optional)
# -----------------------------
def process_batch(batch):
    for item in batch:
        executor.submit(process_single_item, item)

# -----------------------------
# RabbitMQ callback
# -----------------------------
def on_message(ch, method, properties, body):
    try:
        data = json.loads(body)
    except Exception as e:
        logging.error(f"[consumer] Failed to parse message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    with buffer_lock:
        batch_buffer.append(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        if len(batch_buffer) >= BATCH_SIZE:
            to_process = batch_buffer[:]
            batch_buffer.clear()
            # Directly process batch in the main thread (simpler for testing)
            process_batch(to_process)

# -----------------------------
# Run consumer
# -----------------------------
def run_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30
    )

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=PREFETCH_COUNT)
            channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=on_message)

            logging.info("[consumer] Connected to RabbitMQ, waiting for messages...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logging.warning(f"[consumer] RabbitMQ connection failed: {e}, retrying in 3s...")
            time.sleep(3)
        except KeyboardInterrupt:
            logging.info("[consumer] Stopping consumer...")
            break

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    run_consumer()

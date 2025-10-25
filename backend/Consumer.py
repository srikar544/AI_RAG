"""
consumer.py
------------

Purpose:
    Acts as the **task consumer** in the RAG processing pipeline.
    Consumes tasks from RabbitMQ, runs RAG pipeline, and outputs answers.
"""

import pika
import json
import threading
import time
from rag_pipeline import run_pipeline
from config import (
    RABBITMQ_HOST,
    RABBITMQ_QUEUE,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
)

# -------------------------------------------------------------------------
# Core Consumer Function
# -------------------------------------------------------------------------
def process_task(ch, method, properties, body):
    try:
        task = json.loads(body)
        user = task.get("user")
        question = task.get("question")
        pdf_ids = task.get("pdf_ids", ["default.pdf"])

        print(f"\n[Consumer] Received task for user '{user}': {question}")
        for pdf_path in pdf_ids:
            print(f"[Consumer] Processing PDF: {pdf_path}")

        # For now, just pick the first PDF if multiple
        pdf_path = pdf_ids[0] if pdf_ids else "default.pdf"
        result = run_pipeline(question, f"pdfs/{pdf_path}")

        # Log the answer
        print(f"[Consumer] Answer for '{user}':\n{result['answer']}\n")

    except Exception as e:
        print(f"[Consumer] Error processing task: {e}")

    finally:
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)


# -------------------------------------------------------------------------
# Setup RabbitMQ Consumer
# -------------------------------------------------------------------------
def start_consumer():
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

            print("[Consumer] Waiting for tasks. To exit press CTRL+C")
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_task)

            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[Consumer] Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n[Consumer] Stopped by user.")
            break

# -------------------------------------------------------------------------
# Threaded entry point (optional if you want to run multiple consumers)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    start_consumer()

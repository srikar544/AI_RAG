"""
producer.py
------------

Purpose:
    Dynamically sends user questions + PDF references to RabbitMQ as JSON messages.
    Accepts payload from UI or CLI input.
"""

import pika
import json
from typing import Union, List
from config import (
    RABBITMQ_HOST,
    RABBITMQ_QUEUE,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
)

# -------------------------------------------------------------------------
# Core Publisher Function
# -------------------------------------------------------------------------
def send_task(user: str, question: str, pdf_ids: Union[str, List[str], None] = None, retries: int = 5) -> bool:
    if pdf_ids is None:
        pdf_ids = []  # No default PDF, must select explicitly
    elif isinstance(pdf_ids, str):
        pdf_ids = [pdf_ids]

    if not pdf_ids:
        print("[send_task] No PDFs provided, task skipped.")
        return False

    payload = {
        "user": user,
        "question": question,
        "pdf_ids": pdf_ids
    }

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30
    )

    attempt = 0
    while attempt < retries:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

            channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(payload),
                properties=pika.BasicProperties(delivery_mode=2)
            )

            connection.close()
            print(f"[send_task] Task queued: {payload}")
            return True

        except pika.exceptions.AMQPConnectionError as e:
            attempt += 1
            print(f"[send_task] RabbitMQ connection failed (attempt {attempt}/{retries}): {e}")

    print(f"[send_task] Failed to queue task after {retries} attempts: {payload}")
    return False


# -------------------------------------------------------------------------
# Accept JSON Payload (from UI or CLI)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    print("Send JSON payload directly, e.g.:")
    print('{"user": "web_user", "question": "Who is Marcus Aurelius?", "pdf_ids": ["sample.pdf"]}')
    print("Type 'exit' to quit.\n")

    while True:
        raw = input("Enter payload JSON: ")
        if raw.strip().lower() == "exit":
            break
        try:
            data = json.loads(raw)
            user = data.get("user") or "web_user"
            question = data.get("question") or ""
            pdf_ids = data.get("pdf_ids") or []
            send_task(user, question, pdf_ids)
        except json.JSONDecodeError:
            print("Invalid JSON. Please try again.")
        except Exception as e:
            print(f"Error sending task: {e}")

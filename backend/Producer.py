"""
producer.py
------------

Purpose:
    Dynamically sends user questions + PDF references to RabbitMQ as JSON messages.
"""

import pika
import json
import time
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
        pdf_ids = ["default.pdf"]
    elif isinstance(pdf_ids, str):
        pdf_ids = [pdf_ids]

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
            time.sleep(3)

    print(f"[send_task] Failed to queue task after {retries} attempts: {payload}")
    return False

# -------------------------------------------------------------------------
# Dynamic Input Loop for Testing / UI Simulation
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("Enter tasks in JSON format, e.g.:")
    print('{"user": "test_user", "question": "Who is Marcus Aurelius?", "pdf_ids": ["sample.pdf"]}')
    print("Type 'exit' to quit.\n")

    while True:
        raw = input("Enter payload JSON: ")
        if raw.strip().lower() == "exit":
            break
        try:
            data = json.loads(raw)
            user = data.get("user")
            question = data.get("question")
            pdf_ids = data.get("pdf_ids")
            send_task(user, question, pdf_ids)
        except json.JSONDecodeError:
            print("Invalid JSON. Please try again.")
        except Exception as e:
            print(f"Error sending task: {e}")

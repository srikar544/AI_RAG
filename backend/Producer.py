"""
producer.py
------------

Purpose:
    Acts as the **task producer** in the RAG processing pipeline.
    Sends user questions + PDF references to RabbitMQ as JSON messages.

Features:
    - Handles single or multiple PDFs
    - Gracefully handles RabbitMQ connection errors
    - Supports credentials
    - Can be run standalone for testing
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
def send_task(user: str, question: str, pdf_ids: Union[str, List[str], None] = None, retries: int = 3) -> bool:
    """
    Send a user question as a task to RabbitMQ.

    Parameters:
        user (str): User identifier for tracking purposes.
        question (str): The natural-language question.
        pdf_ids (str | list[str] | None): PDFs to query from. Defaults to ["default.pdf"].
        retries (int): Number of retry attempts if RabbitMQ connection fails.

    Returns:
        bool: True if message was successfully sent, False otherwise.
    """

    # -----------------------------
    # 1️⃣ Normalize pdf_ids
    # -----------------------------
    if pdf_ids is None:
        pdf_ids = ["default.pdf"]
    elif isinstance(pdf_ids, str):
        pdf_ids = [pdf_ids]

    # -----------------------------
    # 2️⃣ Build payload
    # -----------------------------
    payload = {
        "user": user,
        "question": question,
        "pdf_ids": pdf_ids
    }

    # -----------------------------
    # 3️⃣ Connect to RabbitMQ & publish
    # -----------------------------
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)

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
            time.sleep(2)

    # -----------------------------
    # 4️⃣ Failed after retries
    # -----------------------------
    print(f"[send_task] Failed to queue task after {retries} attempts: {payload}")
    return False


# -------------------------------------------------------------------------
# Local Test Entry Point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    # Multiple PDFs per question
    send_task("tester", "Give me a summary of the introduction.", ["sample.pdf", "chapter1.pdf"])
    
    # Single PDF
    send_task("tester2", "Explain RAG pipeline", "default.pdf")
    
    # No PDF argument → defaults to ["default.pdf"]
    send_task("tester3", "Test default PDF")

    print("All test tasks sent.")

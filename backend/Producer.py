"""
producer.py
------------

Purpose:
    This module acts as the **task producer** in the RAG processing pipeline.
    It takes user input (question + PDF references) and sends it as a
    serialized JSON message to a RabbitMQ queue.

    The message is later consumed by `consumer.py`, which performs the actual
    retrieval-augmented generation (RAG) logic.

Key Responsibilities:
    1. Accept incoming questions and metadata from users.
    2. Validate and normalize input (ensure pdf_ids is a list).
    3. Serialize data into JSON format.
    4. Publish the message to RabbitMQ with persistent delivery mode.
"""

import pika
import json
from config import RABBITMQ_HOST, RABBITMQ_QUEUE


# -----------------------------------------------------------------------------
# Core Publisher Function
# -----------------------------------------------------------------------------
def send_task(user: str, question: str, pdf_ids=None):
    """
    Send a single user question as a task to RabbitMQ.

    Parameters:
        user (str):
            Identifier of the user who submitted the question.
            Typically used for personalization or tracking.

        question (str):
            The natural-language question to be processed by the RAG pipeline.

        pdf_ids (str | list | None):
            One or more identifiers for the PDFs to query from.
            - If a single string is provided, it will be converted to a list.
            - If not provided, defaults to ["default.pdf"].

    Returns:
        bool:
            True if the message was successfully sent to RabbitMQ.

    Flow:
        1. Validate pdf_ids (convert to list if needed).
        2. Create a JSON payload containing user, question, and pdf_ids.
        3. Establish a connection to RabbitMQ.
        4. Declare the queue (ensures existence).
        5. Publish the message with `delivery_mode=2` for persistence.
        6. Close the connection.
    """

    # -------------------------------------------------------------------------
    # 1️⃣ Ensure pdf_ids is a list
    # -------------------------------------------------------------------------
    if pdf_ids is None:
        pdf_ids = ["default.pdf"]           # default fallback
    elif isinstance(pdf_ids, str):
        pdf_ids = [pdf_ids]                 # normalize single value into list

    # -------------------------------------------------------------------------
    # 2️⃣ Build the message payload
    # -------------------------------------------------------------------------
    payload = {
        "user": user,
        "question": question,
        "pdf_ids": pdf_ids
    }

    # -------------------------------------------------------------------------
    # 3️⃣ Establish RabbitMQ connection and publish the message
    # -------------------------------------------------------------------------
    # Each task is sent to the queue defined in config.RABBITMQ_QUEUE
    # The `durable=True` flag ensures the queue and its messages survive restarts.
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    ch = conn.channel()
    ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    # -------------------------------------------------------------------------
    # 4️⃣ Publish the message
    # -------------------------------------------------------------------------
    ch.basic_publish(
        exchange='',                         # default exchange
        routing_key=RABBITMQ_QUEUE,          # queue name
        body=json.dumps(payload),            # serialize to JSON string
        properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
    )

    # -------------------------------------------------------------------------
    # 5️⃣ Close connection and return success
    # -------------------------------------------------------------------------
    conn.close()
    return True


# -----------------------------------------------------------------------------
# Local Test Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Run this file directly to send a few sample tasks for testing purposes.
    These tasks will appear in the RabbitMQ queue and be picked up by the consumer.
    """
    # ✅ Multiple PDFs per question
    send_task("tester", "Give me a summary of the introduction.", ["sample.pdf", "chapter1.pdf"])
    
    # ✅ Single PDF (auto-wrapped into list)
    send_task("tester2", "Explain RAG pipeline", "default.pdf")
    
    # ✅ No PDF argument → defaults to ["default.pdf"]
    send_task("tester3", "Test default PDF")

    print("Tasks sent")

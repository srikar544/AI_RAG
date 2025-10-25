"""
consumer.py
------------

Purpose:
    Acts as the task consumer in the RAG pipeline.
    Receives user questions + PDF references from RabbitMQ, processes PDFs, and prints answers.
"""

import pika
import json
import os
from rag_pipeline import run_pipeline
from config import RABBITMQ_HOST, RABBITMQ_QUEUE, RABBITMQ_USER, RABBITMQ_PASSWORD

PDF_FOLDER = r"D:\srikardata\AI\AI_RAG\backend\pdfs"  # Use same folder as app.py

# -------------------------------------------------------------------------
# RabbitMQ Consumer Callback
# -------------------------------------------------------------------------
def callback(ch, method, properties, body):
    try:
        task = json.loads(body)
        user = task.get("user", "anonymous")
        question = task.get("question", "")

        # Ensure pdf_ids is a list
        pdf_list = task.get("pdf_ids") or task.get("pdf_id")
        if not pdf_list:
            print(f"[Consumer] No PDF provided for user '{user}', task skipped.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if isinstance(pdf_list, str):
            pdf_list = [pdf_list]

        # Keep only PDFs that exist
        pdf_list = [pdf for pdf in pdf_list if os.path.exists(os.path.join(PDF_FOLDER, pdf))]
        if not pdf_list:
            print(f"[Consumer] No valid PDFs found for user '{user}', task skipped.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"[Consumer] Received task for user '{user}': {json.dumps(task, indent=4)}")

        # Process each PDF
        for pdf in pdf_list:
            pdf_path = os.path.join(PDF_FOLDER, pdf)
            print(f"[Consumer] Processing PDF: {pdf}")
            result = run_pipeline(question, pdf_path)

            # Print the answer
            print(f"[Consumer] Answer for '{user}':\n{result['answer']}\n")

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[Consumer] Error processing task: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# -------------------------------------------------------------------------
# Start RabbitMQ Consumer
# -------------------------------------------------------------------------
def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)

    print("[Consumer] Waiting for tasks. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[Consumer] Exiting...")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()

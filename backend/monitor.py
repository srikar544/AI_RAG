"""
monitor.py
-----------

Purpose:
    This module is a lightweight RabbitMQ queue monitor.
    It periodically checks the length of the task queue (RABBITMQ_QUEUE)
    and prints the number of pending messages every few seconds.

Usage:
    python monitor.py

What it helps with:
    - Quickly verify that your producer is sending tasks.
    - Confirm whether your consumer is keeping up.
    - Helps identify backlog or system load in real time.
"""

import time
import pika
from config import RABBITMQ_HOST, RABBITMQ_QUEUE


def get_queue_length():
    """
    Connects to RabbitMQ and retrieves the number of messages currently
    waiting in the specified queue (RABBITMQ_QUEUE).

    Steps:
    1. Create a connection to RabbitMQ using pika.
    2. Open a channel.
    3. Declare the queue in 'passive' mode — meaning it won’t create the queue
       if it doesn’t already exist; it just checks its status.
    4. Extract the `message_count` which represents the number of messages
       currently waiting in the queue.
    5. Close the connection and return the count.

    Returns:
        int: Number of unprocessed messages in the queue.
    """
    # Step 1: Connect to RabbitMQ
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    
    # Step 2: Open a channel for communication
    ch = conn.channel()
    
    # Step 3: Passive declare just to get queue information, not to create it
    q = ch.queue_declare(queue=RABBITMQ_QUEUE, passive=True)
    
    # Step 4: Extract message count
    length = q.method.message_count

    # Step 5: Close the connection
    conn.close()

    return length


if __name__ == "__main__":
    """
    When executed directly, this script runs an infinite loop:
    - Every 5 seconds, it prints the number of messages in the queue.
    - Helps visualize load and throughput during development or testing.
    """
    while True:
        print("Queue length:", get_queue_length())
        time.sleep(5)

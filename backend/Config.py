"""
config.py
-----------

Central configuration for the RAG pipeline system.

Features:
    - RabbitMQ & Redis connection settings
    - Database configuration
    - Worker and batching parameters
    - Default PDF paths
    - Environment variable overrides for production
"""

import os

# -------------------------------------------------------------------------
# RabbitMQ Settings
# -------------------------------------------------------------------------
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE", "rag_queue")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")       # default user
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")  # default password
RABBITMQ_PREFETCH_COUNT = int(os.environ.get("RABBITMQ_PREFETCH_COUNT", 1))

# -------------------------------------------------------------------------
# Redis Settings (for pub/sub and caching)
# -------------------------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_RESULTS_CHANNEL = os.environ.get("REDIS_RESULTS_CHANNEL", "rag_results_channel")
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 3600))  # 1 hour default

# -------------------------------------------------------------------------
# Database
# -------------------------------------------------------------------------
DB_PATH = os.environ.get("DB_PATH", "sqlite:///rag_results.db")  # SQLite DB URI

# -------------------------------------------------------------------------
# Worker / Batching Settings
# -------------------------------------------------------------------------
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 5))
WORKER_THREAD_POOL = int(os.environ.get("WORKER_THREAD_POOL", 4))

# -------------------------------------------------------------------------
# Placeholder PDF Path (for RAG engine stub or testing)
# -------------------------------------------------------------------------
PDF_PATH = os.environ.get("PDF_PATH", "sample.pdf")

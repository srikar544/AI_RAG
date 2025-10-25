"""
config.py
-----------

Central configuration for the RAG pipeline system.
"""

import os

# -------------------------------------------------------------------------
# RabbitMQ Settings
# -------------------------------------------------------------------------
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE", "rag_queue")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_PREFETCH_COUNT = int(os.environ.get("RABBITMQ_PREFETCH_COUNT", 1))

# -------------------------------------------------------------------------
# Redis Settings
# -------------------------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_RESULTS_CHANNEL = os.environ.get("REDIS_RESULTS_CHANNEL", "rag_results_channel")
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 3600))

# -------------------------------------------------------------------------
# Database
# -------------------------------------------------------------------------
DB_PATH = os.environ.get("DB_PATH", "sqlite:///rag_results.db")

# -------------------------------------------------------------------------
# Worker / Batching Settings
# -------------------------------------------------------------------------
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 1))
WORKER_THREAD_POOL = int(os.environ.get("WORKER_THREAD_POOL", 4))

# -------------------------------------------------------------------------
# Placeholder PDF Path
# -------------------------------------------------------------------------
PDF_PATH = "pdfs/sample.pdf"  # Default PDF to use if none provided

# -------------------------------------------------------------------------
# Alias for backward compatibility
# -------------------------------------------------------------------------
PREFETCH_COUNT = RABBITMQ_PREFETCH_COUNT

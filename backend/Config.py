"""
config.py
-----------

Central configuration file for the RAG pipeline system.
Contains all constants, connection info, and runtime settings.

Purpose:
    - Define RabbitMQ and Redis connection parameters
    - Define caching behavior
    - Define database path
    - Define worker/batching parameters
    - Define default PDF paths for testing or fallback
"""

# -------------------------------------------------------------------------
# RabbitMQ Settings
# -------------------------------------------------------------------------
RABBITMQ_HOST = "localhost"          # RabbitMQ server host
RABBITMQ_QUEUE = "rag_queue"         # Queue name for RAG tasks

# -------------------------------------------------------------------------
# Redis Settings (for pub/sub and caching)
# -------------------------------------------------------------------------
REDIS_HOST = "localhost"             # Redis server host
REDIS_PORT = 6379                    # Redis port
REDIS_DB = 0                         # Redis database index
REDIS_RESULTS_CHANNEL = "rag_results_channel"  # Channel for streaming RAG results to frontend
CACHE_TTL_SECONDS = 3600             # How long to cache answers (in seconds, 1 hour)

# -------------------------------------------------------------------------
# Database
# -------------------------------------------------------------------------
DB_PATH = "sqlite:///rag_results.db"  # SQLite DB URI for query_results table

# -------------------------------------------------------------------------
# Worker / Batching Settings
# -------------------------------------------------------------------------
BATCH_SIZE = 5                        # Number of tasks to accumulate before processing batch
WORKER_THREAD_POOL = 4                # Number of concurrent threads for processing
PREFETCH_COUNT = 1                    # RabbitMQ prefetch count to limit unacked messages

# -------------------------------------------------------------------------
# Placeholder PDF Path (for rag_engine stub or testing)
# -------------------------------------------------------------------------
PDF_PATH = "pdfs/sample.pdf"               # Default PDF to use if none provided

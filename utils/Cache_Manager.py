# cache_manager.py
import redis
import hashlib
import json
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_TTL_SECONDS, REDIS_RESULTS_CHANNEL

_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def _key(question: str, pdf_id: str):
    h = hashlib.sha256(f"{pdf_id}:{question}".encode()).hexdigest()
    return f"rag_cache:{h}"

def get_cached_answer(question: str, pdf_id: str):
    k = _key(question, pdf_id)
    v = _r.get(k)
    return v  # already decoded string or None

def set_cached_answer(question: str, pdf_id: str, answer: str, metadata: dict = None):
    k = _key(question, pdf_id)
    _r.set(k, answer, ex=CACHE_TTL_SECONDS)
    if metadata is not None:
        _r.set(k + ":meta", json.dumps(metadata), ex=CACHE_TTL_SECONDS)

def publish_result(result: dict):
    """
    Publish to Redis channel so the Flask WebSocket server can stream.
    """
    _r.publish(REDIS_RESULTS_CHANNEL, json.dumps(result))

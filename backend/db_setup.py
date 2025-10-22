"""
db_setup.py
------------

Purpose:
    Defines the database model and setup used to store RAG query results.
    Uses SQLAlchemy ORM to create and manage a lightweight SQLite database.

    The `QueryResult` table holds all questions, answers, and related
    metadata — serving as both a logging and caching layer.

Responsibilities:
    ✅ Define the database schema using SQLAlchemy ORM
    ✅ Establish connection to SQLite (or any configured DB)
    ✅ Provide a reusable session factory for DB operations
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import json
from config import DB_PATH


# -------------------------------------------------------------------------
# SQLAlchemy Base Class
# -------------------------------------------------------------------------
Base = declarative_base()


# -------------------------------------------------------------------------
# ORM Model Definition
# -------------------------------------------------------------------------
class QueryResult(Base):
    """
    ORM model representing a single stored query and its generated answer.

    Table Name:
        query_results

    Columns:
        id (int, primary key, auto-increment):
            Unique ID for each stored record.

        user (str):
            The username or identifier of the requester.

        question (text):
            The full text of the user’s query.

        answer (text):
            The generated answer (from RAG pipeline).

        llm_model (str):
            The LLM used for answering (e.g., GPT-3.5, GPT-4).

        cache_hit (bool):
            Indicates if the result came from cache instead of recomputation.

        metadata (text, nullable):
            Additional contextual or diagnostic info.
            Stored as a JSON string (e.g., intent, keywords, runtime, etc.).

        timestamp (datetime):
            When the record was created. Defaults to UTC now.

    Example Entry:
        {
            "id": 12,
            "user": "alice",
            "question": "Summarize chapter 2",
            "answer": "Chapter 2 focuses on ...",
            "llm_model": "GPT-4",
            "cache_hit": False,
            "metadata": "{\"intent\": \"summarization\", \"keywords\": [\"chapter\", \"summary\"]}",
            "timestamp": "2025-10-20T09:22:33"
        }
    """
    __tablename__ = "query_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    llm_model = Column(String)
    cache_hit = Column(Boolean, default=False)
    metadata = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


# -------------------------------------------------------------------------
# Database Engine and Session Factory
# -------------------------------------------------------------------------
# SQLite database path loaded from config.py
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

# Create all tables (runs once at startup)
Base.metadata.create_all(engine)

# Session factory for transactional DB access
SessionLocal = sessionmaker(bind=engine)

# db_setup.py
# ------------

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import DB_PATH

# -------------------------------------------------------------------
# Base class for ORM models
# -------------------------------------------------------------------
Base = declarative_base()

# -------------------------------------------------------------------
# ORM Model: query_results
# -------------------------------------------------------------------
class QueryResult(Base):
    __tablename__ = "query_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    llm_model = Column(String)
    cache_hit = Column(Boolean, default=False)
    meta_info = Column(Text, nullable=True)  # Stores extra metadata
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# -------------------------------------------------------------------
# Database engine and session
# -------------------------------------------------------------------
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)  # Create tables if they don't exist
SessionLocal = sessionmaker(bind=engine)

<<<<<<< HEAD
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime, Boolean
)
=======
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean
>>>>>>> 8712733b18d7141c0262a85d4efe2637a83e4559
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import DB_PATH

<<<<<<< HEAD
Base = declarative_base()

=======
# 1️⃣ Declare the Base class before any models
Base = declarative_base()

# 2️⃣ Define your ORM model
>>>>>>> 8712733b18d7141c0262a85d4efe2637a83e4559
class QueryResult(Base):
    __tablename__ = "query_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    llm_model = Column(String)
    cache_hit = Column(Boolean, default=False)
<<<<<<< HEAD
    extra_metadata = Column(Text, nullable=True)  # renamed from metadata
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


# Database engine and session
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

# Create tables
Base.metadata.create_all(engine)

# Session factory
=======
    meta_info = Column("metadata", Text, nullable=True)  # fixed metadata conflict
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# 3️⃣ Create engine and session factory
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
>>>>>>> 8712733b18d7141c0262a85d4efe2637a83e4559
SessionLocal = sessionmaker(bind=engine)

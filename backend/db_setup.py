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
            Python attribute renamed to `meta_info` to avoid SQLAlchemy conflict.

        timestamp (datetime):
            When the record was created. Defaults to UTC now.
    """
    __tablename__ = "query_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    llm_model = Column(String)
    cache_hit = Column(Boolean, default=False)
    meta_info = Column("metadata", Text, nullable=True)  # <-- fixed
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

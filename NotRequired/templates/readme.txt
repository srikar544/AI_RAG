# RAG Pipeline with Dynamic LLM Selection

## Features
- RAG pipeline with PDF embeddings (FAISS)
- RabbitMQ queue for asynchronous processing
- SQLite DB for storing queries & answers
- Dynamic LLM selection:
  - GPT-3.5 for simple/medium questions
  - GPT-4 for complex questions
- Flask frontend dashboard


## Requirements
- Python 3.10+
- RabbitMQ installed and running locally
- OpenAI API key

```bash
pip install -r requirements.txt

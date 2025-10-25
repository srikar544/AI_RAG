"""
rag_pipeline.py
----------------
RAG pipeline using local PDF content. No LLM used; outputs context-based answers.
"""

import os
import PyPDF2

# STEP 1: METADATA EXTRACTION
def extract_metadata(question: str):
    length = len(question)
    keywords = [w for w in question.split() if len(w) > 5][:8]
    qlower = question.lower()

    if any(kw in qlower for kw in ["summarize", "summary", "summarise"]):
        intent = "summarization"
    elif any(kw in qlower for kw in ["how", "why", "explain"]):
        intent = "explanatory"
    elif any(kw in qlower for kw in ["list", "what", "who", "when"]):
        intent = "factual"
    else:
        intent = "general"

    return {"intent": intent, "keywords": keywords, "length": length}

# STEP 2: BUILD PROMPT
def build_dynamic_prompt(question: str, metadata: dict):
    intent = metadata.get("intent", "general")
    keywords = ", ".join(metadata.get("keywords", [])) or "None"

    prompt = (
        f"You are an assistant answering based on a provided PDF document.\n"
        f"Intent: {intent}\n"
        f"Keywords: {keywords}\n\n"
        f"Question: {question}\n\n"
        f"Please answer concisely and cite relevant document snippets if applicable."
    )
    return prompt

# STEP 3: MODEL SELECTION
def select_model(question: str, metadata: dict):
    if metadata.get("intent") == "summarization" or metadata.get("length", 0) > 250:
        return "GPT-4"
    return "GPT-3.5"

# STEP 4: LOAD PDF & SPLIT TEXT
def load_pdf_text(pdf_path: str):
    if not os.path.exists(pdf_path):
        return []

    text_chunks = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                words = text.split()
                chunk_size = 200
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    text_chunks.append(chunk)
    return text_chunks

# STEP 5: RETRIEVE CONTEXT
def retrieve_context(chunks, question, top_k=3):
    question_keywords = [w.lower() for w in question.split() if len(w) > 3]
    scored_chunks = []
    for chunk in chunks:
        score = sum(chunk.lower().count(kw) for kw in question_keywords)
        if score > 0:
            scored_chunks.append((score, chunk))
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    top_chunks = [c for _, c in scored_chunks[:top_k]]
    if not top_chunks:
        top_chunks = chunks[:top_k]
    return top_chunks

# STEP 6: GENERATE ANSWER
def generate_answer(context_chunks, prompt):
    context = "\n\n".join(context_chunks)
    return f"{context}\n\nAnswer: Based on the document context, {prompt}"

# STEP 7: RUN PIPELINE FOR SINGLE PDF
def run_pipeline(question: str, pdf_path: str):
    metadata = extract_metadata(question)
    prompt = build_dynamic_prompt(question, metadata)
    model = select_model(question, metadata)

    chunks = load_pdf_text(pdf_path)
    ctx = retrieve_context(chunks, question, top_k=3)
    answer = generate_answer(ctx, prompt)

    return {"answer": answer, "metadata": metadata, "llm_model": model}

"""
rag_pipeline.py
----------------

Purpose:
    This module defines the **RAG orchestration pipeline**.
    It coordinates the key steps required to transform a raw user question
    into an actionable LLM query augmented by retrieval.

Pipeline Responsibilities:
    1. Extract metadata and context from the user question.
    2. Dynamically build a prompt with metadata and intent clues.
    3. Select the most suitable LLM model for the query type.
    4. Execute retrieval-augmented generation via `rag_engine.run_rag()`.

The output is a structured dictionary containing:
    {
        "answer": <model output>,
        "metadata": <analysis about question>,
        "llm_model": <which model was selected>
    }
"""

import json
import random
from rag_engine import run_rag


# -------------------------------------------------------------------------
# STEP 1: METADATA EXTRACTION
# -------------------------------------------------------------------------
def extract_metadata(question: str):
    """
    Perform lightweight metadata extraction from the user’s question.

    Returns:
        dict: {
            "intent":  The detected type of question (e.g., summarization, factual),
            "keywords": Top keywords for context retrieval,
            "length":  Number of characters in the question.
        }

    Details:
        - Uses very naive heuristics (string checks).
        - In a real RAG system, this could be replaced with:
            * Named Entity Recognition (NER)
            * Intent classification model
            * Keyword extraction (TF-IDF, spaCy, etc.)
    """
    length = len(question)
    # pick words longer than 5 chars, limit to 8 for brevity
    keywords = [w for w in question.split() if len(w) > 5][:8]

    qlower = question.lower()

    # Naive intent classification
    if any(kw in qlower for kw in ["summarize", "summary", "summarise"]):
        intent = "summarization"
    elif any(kw in qlower for kw in ["how", "why", "explain"]):
        intent = "explanatory"
    elif any(kw in qlower for kw in ["list", "what", "who", "when"]):
        intent = "factual"
    else:
        intent = "general"

    return {"intent": intent, "keywords": keywords, "length": length}


# -------------------------------------------------------------------------
# STEP 2: PROMPT BUILDING
# -------------------------------------------------------------------------
def build_dynamic_prompt(question: str, metadata: dict):
    """
    Construct a custom LLM prompt by combining metadata and the question.

    Purpose:
        Helps the downstream LLM understand the type of task and relevant cues.
        The structure can easily be adapted for persona-based or chain-of-thought
        prompting strategies.

    Example Output:
        "You are an assistant answering based on a provided document.
         Intent: summarization
         Keywords: introduction, overview, background

         Question: Summarize the introduction section of the PDF.

         Please answer concisely and cite relevant document snippets if applicable."
    """
    intent = metadata.get("intent", "general")
    keywords = ", ".join(metadata.get("keywords", [])) or "None"

    prompt = (
        f"You are an assistant answering based on a provided document.\n"
        f"Intent: {intent}\n"
        f"Keywords: {keywords}\n\n"
        f"Question: {question}\n\n"
        f"Please answer concisely and cite relevant document snippets if applicable."
    )
    return prompt


# -------------------------------------------------------------------------
# STEP 3: MODEL SELECTION
# -------------------------------------------------------------------------
def select_model(question: str, metadata: dict):
    """
    Choose which LLM model should be used based on question characteristics.

    Heuristic:
        - Long or summarization-style queries → use GPT-4.
        - Short/factual queries → use GPT-3.5.

    Returns:
        str: The model name ("GPT-4" or "GPT-3.5").
    """
    if metadata.get("intent") == "summarization" or metadata.get("length", 0) > 250:
        return "GPT-4"
    return "GPT-3.5"


# -------------------------------------------------------------------------
# STEP 4: PIPELINE EXECUTION
# -------------------------------------------------------------------------
def run_pipeline(question: str, pdf_id: str):
    """
    Orchestrate the complete RAG flow for a single question + PDF.

    Steps:
        1. Extract metadata from the question.
        2. Build a dynamic LLM prompt.
        3. Select an appropriate model (informational use).
        4. Call the RAG engine (retrieval + generation).
        5. Return structured results.

    Parameters:
        question (str): The user question.
        pdf_id (str): Identifier for the target PDF/document.

    Returns:
        dict: {
            "answer":  Generated text answer from RAG engine,
            "metadata": Metadata used to shape the prompt,
            "llm_model": Which model was selected
        }
    """
    # 1️⃣ Metadata extraction
    metadata = extract_metadata(question)

    # 2️⃣ Build final prompt
    prompt = build_dynamic_prompt(question, metadata)

    # 3️⃣ Model selection (currently informational only)
    model = select_model(question, metadata)

    # 4️⃣ Run the RAG engine (retrieval + generation)
    # Note: run_rag() internally handles PDF retrieval & LLM inference.
    answer = run_rag(prompt, pdf_id)

    # 5️⃣ Package results
    return {"answer": answer, "metadata": metadata, "llm_model": model}

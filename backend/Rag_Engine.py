# rag_engine.py (realistic version)
import PyPDF2

def load_pdf_text(pdf_path: str):
    text_chunks = []
    with open(pdf_path, 'rb') as f:
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

def generate_answer(context_chunks, prompt):
    context = "\n\n".join(context_chunks)
    return f"{context}\n\nAnswer: Based on the document context, {prompt}"

def run_rag(prompt: str, pdf_path: str):
    chunks = load_pdf_text(pdf_path)
    ctx = retrieve_context(chunks, prompt, top_k=3)
    return generate_answer(ctx, prompt)

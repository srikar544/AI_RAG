def build_prompt(question: str, metadata: dict):
    prompt = f"""
    You are an intelligent assistant.
    User intent: {metadata['intent']}
    Question complexity: {metadata['length']} characters
    Key terms: {', '.join(metadata['keywords'][:5])}

    Now respond accurately and concisely to the question below:
    {question}
    """
    return prompt.strip()

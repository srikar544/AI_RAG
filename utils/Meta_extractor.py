def extract_metadata(question: str):
    metadata = {}
    metadata["length"] = len(question)
    metadata["keywords"] = [w for w in question.split() if len(w) > 5]
    metadata["intent"] = (
        "fact" if "when" in question or "who" in question else "explanation"
    )
    return metadata

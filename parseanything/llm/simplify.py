from parseanything.registry import get_llm_backend

def simplify_text(text: str) -> str:
    llm = get_llm_backend("ollama")
    if not llm:
        return "LLM backend not available."
    
    prompt = f"Rewrite the following text in very simple, plain English that a 10-year-old could understand. Do not add any new information, just simplify the vocabulary and grammar:\n\n{text}"
    try:
        return llm.generate(prompt)
    except Exception as e:
        return f"Error simplifying: {e}"

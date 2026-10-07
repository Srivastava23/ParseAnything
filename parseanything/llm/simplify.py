from parseanything.registry import get_llm_backend

def simplify_text(text: str) -> str:
    from parseanything.config import Options
    from parseanything.llm.backends import OllamaLLMBackend
    llm = get_llm_backend("ollama")
    if not llm:
        opts = Options()
        llm = OllamaLLMBackend(opts)
    
    prompt = (
        "Rewrite the following text in very simple, plain English that a 10-year-old could understand. "
        "Provide ONLY the simplified explanation directly. Do NOT include any introductory lines, preambles, "
        "or conversational filler like 'Here is a rewritten version...'.\n\n"
        f"{text}"
    )
    try:
        import re
        raw = llm.generate(prompt).strip()
        # Strip common conversational preambles
        cleaned = re.sub(r'^(here is (a |the )?(rewritten|simplified|simpler)[^\n:]*[:\n]+)', '', raw, flags=re.IGNORECASE).strip()
        lines = cleaned.splitlines()
        if lines and lines[0].strip().endswith(":") and len(lines) > 1:
            first = lines[0].strip().lower()
            if any(k in first for k in ["here is", "rewritten", "simplified", "plain english", "summary", "version of"]):
                cleaned = "\n".join(lines[1:]).strip()
        return cleaned or raw
    except Exception as e:
        return f"Error simplifying: {e}"

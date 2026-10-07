from pydantic import BaseModel
from parseanything.schema import Document
from parseanything.registry import get_llm_backend

class QuestionsResponse(BaseModel):
    questions: list[str]

def generate_next_questions(doc: Document) -> list[str]:
    fallback_questions = [
        "What are the main entities mentioned in this document?",
        "Can you summarize the key action items?",
        "What is the overall tone or sentiment?"
    ]
    
    from parseanything.config import Options
    from parseanything.llm.backends import OllamaLLMBackend, OpenAILLMBackend
    opts = Options()
    if opts.llm.backend == "openai":
        llm = OpenAILLMBackend(opts)
    else:
        llm = OllamaLLMBackend(opts)
        
    domain = doc.analysis.get("domain", "general")
    
    # Extract excerpt of text from document blocks
    texts = []
    for page in doc.pages[:3]:
        for block in page.blocks:
            if block.content and block.content.strip():
                texts.append(block.content.strip())
    doc_excerpt = "\n".join(texts)[:1200]
    
    prompt = f"""Given the following document text (classified as '{domain}' domain):
---
{doc_excerpt}
---

Suggest exactly 3 to 4 specific, insightful questions that a user would naturally ask about this document. Return JSON matching the schema."""
    
    try:
        result = llm.generate_json(prompt, QuestionsResponse)
        if hasattr(result, "questions") and len(result.questions) > 0:
            return result.questions
        return fallback_questions
    except Exception as e:
        print(f"LLM Error generating questions: {e}")
        return fallback_questions

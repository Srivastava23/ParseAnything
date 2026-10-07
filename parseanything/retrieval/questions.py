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
    
    llm = get_llm_backend("ollama")
    if not llm:
        return fallback_questions
        
    domain = doc.analysis.get("domain", "general")
    
    # Try to extract actual custom topics from the document if available
    topics = []
    for page in doc.pages[:2]:
        for block in page.blocks:
            if block.type == "heading" and len(block.content) > 5:
                topics.append(block.content)
    
    prompt = f"Based on this document which is identified as '{domain}' domain, suggest exactly 3 to 5 relevant follow-up questions the user might want to ask about its contents. Return a JSON array of strings."
    
    try:
        result = llm.generate_json(prompt, QuestionsResponse)
        if hasattr(result, "questions") and len(result.questions) > 0:
            return result.questions
        return fallback_questions
    except Exception:
        if topics:
            return [
                f"What are the key takeaways regarding {topics[0]}?",
                f"Can you provide more details about {topics[1] if len(topics) > 1 else 'the main subject'}?",
                "What is the overall conclusion of this document?"
            ]
        return fallback_questions

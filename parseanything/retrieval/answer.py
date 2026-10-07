from pydantic import BaseModel, Field
from typing import Optional
import re
from parseanything.schema import Document
from parseanything.config import Options
from parseanything.llm.backends import OllamaLLMBackend, OpenAILLMBackend
from parseanything.retrieval.store import SQLiteRetriever

class AnswerClaim(BaseModel):
    text: str = Field(description="The factual claim made")
    citations: list[str] = Field(description="List of block IDs cited for this claim, e.g. ['b_123', 'b_456']")

class AnswerResponse(BaseModel):
    answer: str = Field(description="The complete answer with inline [B:id] markers")
    claims: list[AnswerClaim] = Field(description="Individual claims extracted from the answer")

class ValidatedAnswer(BaseModel):
    answer: str
    unsupported_claims: list[str]
    errors: list[str]

def validate_answer(response: AnswerResponse, retrieved_blocks: dict) -> ValidatedAnswer:
    unsupported = []
    errors = []
    
    markers = re.findall(r'\[B:(.*?)\]', response.answer)
    for m in markers:
        if m not in retrieved_blocks:
            errors.append(f"Cited block {m} not in retrieved context")
            
    for claim in response.claims:
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', claim.text)
        if not numbers:
            continue
            
        supported = False
        for cid in claim.citations:
            if cid in retrieved_blocks:
                block_text = retrieved_blocks[cid].content
                all_found = all(n in block_text for n in numbers)
                if all_found:
                    supported = True
                    break
        if not supported:
            unsupported.append(claim.text)
            
    return ValidatedAnswer(answer=response.answer, unsupported_claims=unsupported, errors=errors)

def ask_question(doc: Document, question: str, opts: Options) -> ValidatedAnswer:
    retriever = SQLiteRetriever(doc, opts)
    results = retriever.search(question, k=5)
    
    retrieved_blocks = {r['block'].id: r['block'] for r in results}
    
    context_str = ""
    for r in results:
        b = r['block']
        context_str += f"--- Block {b.id} ---\nSection: {r['path']}\nContent: {b.content}\n\n"
        
    prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context does not contain the answer, say "I don't know".
When stating facts, cite the source block using inline markers like [B:block_id].

Context:
{context_str}

Question: {question}
"""
    
    if opts.llm.backend == "openai":
        llm = OpenAILLMBackend(opts)
    else:
        llm = OllamaLLMBackend(opts)
        
    try:
        response = llm.generate_json(prompt, AnswerResponse)
        if isinstance(response, dict):
            response = AnswerResponse(**response)
        validated = validate_answer(response, retrieved_blocks)
        return validated
    except Exception as e:
        return ValidatedAnswer(answer=f"Failed to generate answer: {str(e)}", unsupported_claims=[], errors=[str(e)])

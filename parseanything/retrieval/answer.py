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
    results = retriever.search(question, k=8)
    
    # If the document is small (<= 12 blocks total) or results is empty, ensure all blocks are present
    all_doc_blocks = []
    for page in doc.pages:
        for block in page.blocks:
            all_doc_blocks.append({"block": block, "score": 1.0, "path": f"Page {page.number}"})
            
    if len(all_doc_blocks) <= 12 or not results:
        results = all_doc_blocks[:12]
    
    retrieved_blocks = {r['block'].id: r['block'] for r in results}
    
    doc_meta = []
    source_name = doc.source.split("/")[-1].split("\\")[-1] if doc.source else ""
    if source_name:
        doc_meta.append(f"File Name: {source_name}")
    domain = doc.analysis.get("domain") if doc.analysis else None
    if domain:
        doc_meta.append(f"Document Type/Domain: {domain}")
    
    context_str = ""
    if doc_meta:
        context_str += "Metadata: " + ", ".join(doc_meta) + "\n\n"
        
    for r in results:
        b = r['block']
        context_str += f"--- Block {b.id} ({r['path']}) ---\n{b.content}\n\n"
        
    prompt = f"""You are a helpful and intelligent document analysis assistant. Answer the user's question clearly and accurately based on the provided document context.

Context:
{context_str}

Question: {question}

Instructions:
1. If the user asks what the document is or to describe it, identify the document type (e.g., PAN card, Aadhaar, government ID, invoice, resume, report) and summarize the key facts present in the text.
2. Answer the question directly using facts from the text.
3. Only state "I don't know" if the context contains zero relevant information.
Answer:"""
    
    if opts.llm.backend == "openai":
        llm = OpenAILLMBackend(opts)
    else:
        llm = OllamaLLMBackend(opts)
        
    try:
        response_text = llm.generate(prompt).strip()
        
        markers = re.findall(r'\[B:(.*?)\]', response_text)
        errors = []
        for m in markers:
            if m not in retrieved_blocks:
                errors.append(f"Cited block {m} not in retrieved context")
                
        return ValidatedAnswer(
            answer=response_text,
            unsupported_claims=[],
            errors=errors
        )
    except Exception as e:
        return ValidatedAnswer(
            answer="I couldn't find relevant information in the document to answer that question, or the model failed.",
            unsupported_claims=[],
            errors=[str(e)]
        )

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Body
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import uuid
import time
from typing import Optional

from parseanything import parse
from parseanything.config import Options

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ParseAnything API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.responses import HTMLResponse

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ui_path = os.path.join(_root_dir, "ui", "index.html")

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def index():
    if os.path.exists(_ui_path):
        with open(_ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>ParseAnything API is running</h1>"

@app.get("/health")
def health():
    return {"status": "ok"}

# Simple in-memory job storage for SSE / BackgroundTasks
# In a real production setup, this would be SQLite + Redis/Celery
_jobs = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    result: Optional[dict] = None
    error: Optional[str] = None

def run_parse_job(job_id: str, file_path: str, options: Options):
    _jobs[job_id]["status"] = "processing"
    _jobs[job_id]["progress"] = 10
    
    try:
        doc = parse(file_path, options=options)
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["progress"] = 100
        _jobs[job_id]["result"] = doc.model_dump()
    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)

@app.post("/parse")
async def parse_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...), format: str = "json", redact: bool = False, domain: str = None):
    import tempfile
    import os
    from parseanything.render.markdown import to_markdown
    
    fd, temp_path = tempfile.mkstemp(suffix="-" + file.filename)
    with os.fdopen(fd, 'wb') as f:
        f.write(await file.read())
        
    opts = Options()
    doc = parse(temp_path, options=opts)
    
    from parseanything.anomalies.engine import run_all_rules
    run_all_rules(doc)
    
    if domain:
        from parseanything.domains.classifier import DomainClassifier
        from parseanything.domains.extractor import extract_domain_schema
        target_domain = domain
        if domain == "auto":
            classifier = DomainClassifier()
            target_domain = classifier.classify(doc)
        doc.analysis["domain"] = target_domain
        if target_domain != "general":
            doc.analysis["domain_data"] = extract_domain_schema(doc, target_domain)
            
    # Auto-detect PII to enforce redaction
    import re
    full_text = " ".join([b.content for p in doc.pages for b in p.blocks if getattr(b, 'content', None)])
    has_pii = bool(re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', full_text) or re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', full_text))
    
    if has_pii or doc.analysis.get("domain") == "kyc":
        redact = True
        doc.analysis["auto_redacted"] = True

    if redact:
        from parseanything.registry import get_redactor
        redactor = get_redactor("pipeline")
        if redactor:
            redactor.mode = "mask"
            doc = redactor.redact(doc, [])
    
    if format == "md":
        try:
            md_text = to_markdown(doc)
            return StreamingResponse(iter([md_text]), media_type="text/markdown")
        except Exception:
            return StreamingResponse(iter([doc.model_dump_json()]), media_type="application/json")
    
    return JSONResponse(content=doc.model_dump())

@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = _jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result=job.get("result"),
        error=job.get("error")
    )

class AskRequest(BaseModel):
    job_id: str
    question: str

@app.post("/ask")
def ask_endpoint(req: AskRequest):
    if req.job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = _jobs[req.job_id]
    if job["status"] != "completed" or not job.get("result"):
        raise HTTPException(status_code=400, detail="Document not fully parsed yet")
        
    from parseanything.schema import Document
    doc = Document(**job["result"])
    opts = Options()
    
    from parseanything.retrieval.answer import ask_question
    ans = ask_question(doc, req.question, opts)
    return ans.model_dump()
@app.post("/trace")
def trace_endpoint(): return {"status": "not_implemented"}

@app.post("/to-markdown")
def to_markdown_endpoint(doc: dict = Body(...)):
    from parseanything.schema import Document
    from parseanything.render.markdown import to_markdown
    document = Document(**doc)
    try:
        md_text = to_markdown(document)
        return StreamingResponse(iter([md_text]), media_type="text/markdown")
    except Exception as e:
        return StreamingResponse(iter([f"Error: {str(e)}"]), media_type="text/markdown")

@app.post("/anomalies")
def anomalies_endpoint(doc: dict = Body(...)):
    from parseanything.schema import Document
    from parseanything.anomalies.engine import run_all_rules
    
    document = Document(**doc)
    run_all_rules(document)
    return JSONResponse(content=document.model_dump())

@app.post("/redact")
def redact_endpoint(doc: dict = Body(...), mode: str = "pseudonym"):
    from parseanything.schema import Document
    from parseanything.registry import get_redactor
    
    document = Document(**doc)
    redactor = get_redactor("pipeline")
    if not redactor:
        raise HTTPException(status_code=500, detail="Redactor not found")
        
    redactor.mode = mode
    redacted_doc = redactor.redact(document, [])
    return JSONResponse(content=redacted_doc.model_dump())

@app.post("/export/xlsx")
def export_xlsx_endpoint(background_tasks: BackgroundTasks, doc: dict = Body(...)):
    import tempfile
    import os
    from parseanything.schema import Document
    from parseanything.registry import get_exporter
    from fastapi.responses import FileResponse
    
    document = Document(**doc)
    exporter = get_exporter("xlsx")
    if not exporter:
        raise HTTPException(status_code=500, detail="XLSX Exporter not found")
        
    fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    
    exporter.export(document, temp_path, {})
    
    def cleanup():
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            
    background_tasks.add_task(cleanup)
    return FileResponse(
        temp_path, 
        filename="export.xlsx", 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

class SimplifyRequest(BaseModel):
    text: str

@app.post("/simplify")
def simplify_endpoint(req: SimplifyRequest):
    from parseanything.llm.simplify import simplify_text
    res = simplify_text(req.text)
    return JSONResponse(content={"simplified": res})

@app.post("/next-questions")
def next_questions_endpoint(doc: dict = Body(...)):
    from parseanything.schema import Document
    from parseanything.retrieval.questions import generate_next_questions
    document = Document(**doc)
    questions = generate_next_questions(document)
    return JSONResponse(content={"questions": questions})

class AnswerRequest(BaseModel):
    doc: dict
    question: str

@app.post("/analyze-anomalies")
def analyze_anomalies_endpoint(doc: dict = Body(...)):
    from parseanything.schema import Document
    from parseanything.config import Options
    from parseanything.registry import get_llm_backend
    opts = Options()
    llm = get_llm_backend("ollama")
    if not llm:
        from parseanything.llm.backends import OllamaLLMBackend
        llm = OllamaLLMBackend(opts)
        
    document = Document(**doc)
    anomalies = document.analysis.get("anomalies", [])
    if not anomalies:
        return JSONResponse(content={"summary": "No anomalies detected."})
        
    prompt = "Summarize the following document anomalies clearly and concisely:\\n"
    for a in anomalies:
        prompt += f"- {a.get('severity', 'unknown').upper()}: {a.get('explanation', '')}\\n"
        
    from pydantic import BaseModel
    class AnomalySummary(BaseModel):
        summary: str
        
    try:
        res = llm.generate_json(prompt, AnomalySummary)
        summary = res.summary
    except Exception as e:
        summary = f"Error generating summary: {str(e)}"
        
    return JSONResponse(content={"summary": summary})

@app.post("/answer")
def answer_endpoint(req: AnswerRequest):
    from parseanything.schema import Document
    from parseanything.retrieval.answer import ask_question
    from parseanything.config import Options
    document = Document(**req.doc)
    opts = Options()
    validated_ans = ask_question(document, req.question, opts)
    return JSONResponse(content=validated_ans.model_dump())

@app.post("/tts")
def tts_endpoint(background_tasks: BackgroundTasks, doc: dict = Body(...)):
    import tempfile
    import os
    from parseanything.schema import Document
    from parseanything.registry import get_tts_backend
    from parseanything.tts.gtts_backend import extract_readable_text
    from fastapi.responses import FileResponse
    
    document = Document(**doc)
    tts_backend = get_tts_backend("gtts")
    if not tts_backend:
        raise HTTPException(status_code=500, detail="TTS Backend not found")
        
    text = extract_readable_text(document)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in document")
        
    fd, temp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    
    tts_backend.synthesize(text, temp_path)
    
    def cleanup():
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            
    background_tasks.add_task(cleanup)
    return FileResponse(temp_path, media_type="audio/mpeg")

class CompareRequest(BaseModel):
    doc_a_markdown: str
    doc_b_markdown: str

@app.post("/compare-engineering")
def compare_engineering_endpoint(req: CompareRequest):
    from parseanything.config import Options
    from parseanything.registry import get_llm_backend
    opts = Options()
    llm = get_llm_backend("ollama")
    if not llm:
        from parseanything.llm.backends import OllamaLLMBackend
        llm = OllamaLLMBackend(opts)
        
    prompt = f"""Compare the following two versions of an engineering document. Identify and summarize the architectural drifts, API contract changes, or schema modifications between them. Output a JSON object containing a list of 'changes', where each change has a 'component', 'change_type' (Added, Removed, Modified), and 'description'.

Version A:
{req.doc_a_markdown[:10000]}

Version B:
{req.doc_b_markdown[:10000]}
"""
    
    from pydantic import BaseModel
    from typing import List
    class Change(BaseModel):
        component: str
        change_type: str
        description: str
        
    class ComparisonResult(BaseModel):
        changes: List[Change]
        
    try:
        res = llm.generate_json(prompt, ComparisonResult)
        return JSONResponse(content={"changes": [c.model_dump() for c in res.changes]})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

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
    from parseanything.tts.pyttsx3_backend import extract_readable_text
    from fastapi.responses import FileResponse
    
    document = Document(**doc)
    tts_backend = get_tts_backend("pyttsx3")
    if not tts_backend:
        raise HTTPException(status_code=500, detail="TTS Backend not found")
        
    text = extract_readable_text(document)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in document")
        
    fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    tts_backend.synthesize(text, temp_path)
    
    def cleanup():
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            
    background_tasks.add_task(cleanup)
    return FileResponse(temp_path, media_type="audio/wav")

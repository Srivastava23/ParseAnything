from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import uuid
import time
from typing import Optional

from parseanything import parse
from parseanything.config import Options

app = FastAPI(title="ParseAnything API")

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

@app.post("/parse", response_model=JobStatus)
async def parse_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "queued", "progress": 0}
    
    # Save file to temp
    import tempfile
    import os
    
    fd, temp_path = tempfile.mkstemp(suffix="-" + file.filename)
    with os.fdopen(fd, 'wb') as f:
        f.write(await file.read())
        
    opts = Options()
    background_tasks.add_task(run_parse_job, job_id, temp_path, opts)
    return JobStatus(job_id=job_id, status="queued", progress=0)

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
def anomalies_endpoint(): return {"status": "not_implemented"}

@app.post("/redact")
def redact_endpoint(): return {"status": "not_implemented"}

@app.post("/export/xlsx")
def export_xlsx_endpoint(): return {"status": "not_implemented"}

@app.post("/simplify")
def simplify_endpoint(): return {"status": "not_implemented"}

@app.post("/next-questions")
def next_questions_endpoint(): return {"status": "not_implemented"}

@app.post("/tts")
def tts_endpoint(): return {"status": "not_implemented"}

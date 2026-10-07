from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from parseanything import parse
from parseanything.config import Options
from parseanything.registry import _ocr_backends, _layout_backends, _vlm_backends, _format_parsers

app = FastAPI(title="ParseAnything API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/parse")
async def parse_endpoint(
    file: UploadFile = File(...),
    format: str = Query("json", description="Output format: json|md"),
    workers: int = Form(4),
    ocr_backend: str = Form("rapidocr"),
    no_vlm: bool = Form(False)
):
    opts = Options(
        workers=workers,
        ocr_backend=ocr_backend,
        vlm_backend="stub_vlm" if no_vlm else "vlm"
    )
    
    content = await file.read()
    doc = parse(content, options=opts, extension_hint=file.filename)
    
    if doc.errors and any(not e.recoverable for e in doc.errors):
        return JSONResponse(status_code=500, content={"errors": [e.model_dump() for e in doc.errors]})
        
    if format == "md":
        try:
            from parseanything.render.markdown import to_markdown
            return PlainTextResponse(to_markdown(doc))
        except ImportError:
            raise HTTPException(status_code=501, detail="Markdown rendering not implemented yet.")
            
    return doc.model_dump()

import os
from fastapi.responses import HTMLResponse, FileResponse

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ui_path = os.path.join(_root_dir, "ui", "index.html")

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def index():
    if os.path.exists(_ui_path):
        with open(_ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>ParseAnything API is running</h1><p>Visit <a href='/docs'>/docs</a> for Swagger UI.</p>"

@app.get("/fixture/{name}")
def get_fixture(name: str):
    target = os.path.join(_root_dir, name)
    if os.path.exists(target):
        return FileResponse(target)
    raise HTTPException(status_code=404, detail="Fixture not found")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/backends")
def backends():
    return {
        "ocr": list(_ocr_backends.keys()),
        "layout": list(_layout_backends.keys()),
        "vlm": list(_vlm_backends.keys()),
        "parsers": list(_format_parsers.keys())
    }

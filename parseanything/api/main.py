from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from parseanything import parse
from parseanything.config import Options
from parseanything.registry import _ocr_backends, _layout_backends, _vlm_backends, _format_parsers

app = FastAPI(title="ParseAnything API")

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

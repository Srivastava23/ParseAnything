import typer
from pathlib import Path
from parseanything import parse
from parseanything.config import Options

app = typer.Typer()

@app.command("parse")
def parse_cmd(
    path: str = typer.Argument(..., help="Path to the document to parse"),
    out: Path = typer.Option(..., "--out", help="Output directory"),
    format: str = typer.Option("both", "--format", help="Output format: json|md|both"),
    workers: int = typer.Option(4, "--workers", help="Number of workers for parallel processing"),
    ocr_backend: str = typer.Option("rapidocr", "--ocr-backend", help="OCR backend name"),
    no_vlm: bool = typer.Option(False, "--no-vlm", help="Disable VLM usage")
):
    opts = Options(
        workers=workers,
        ocr_backend=ocr_backend,
        vlm_backend="stub_vlm" if no_vlm else "vlm"
    )
    
    try:
        doc = parse(path, options=opts)
        
        if doc.errors and any(not e.recoverable for e in doc.errors):
            typer.echo("Fatal error occurred during parsing.")
            for e in doc.errors:
                typer.echo(f"[{e.code}] {e.message}")
            raise typer.Exit(code=1)
            
        out.mkdir(parents=True, exist_ok=True)
        base_name = Path(path).stem
        
        if format in ["json", "both"]:
            out_json = out / f"{base_name}.json"
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(doc.model_dump_json(indent=2))
                
        if format in ["md", "both"]:
            try:
                from parseanything.render.markdown import to_markdown
                md_text = to_markdown(doc)
                out_md = out / f"{base_name}.md"
                with open(out_md, "w", encoding="utf-8") as f:
                    f.write(md_text)
            except ImportError:
                typer.echo("Markdown rendering not implemented yet (Agent 4 task).")
                
        typer.echo(f"Parse complete: {doc.stats.pages} pages, {doc.stats.blocks} blocks, {doc.stats.flagged_blocks} flagged.")
        typer.echo(f"Elapsed: {doc.stats.elapsed_s:.2f}s ({doc.stats.pages_per_sec:.2f} pages/sec)")
        
    except Exception as e:
        typer.echo(f"Error: {str(e)}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

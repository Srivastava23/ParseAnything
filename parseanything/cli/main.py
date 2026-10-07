import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from parseanything import parse
from parseanything.config import Options

def run_parse(
    path: str,
    out: Path,
    format: str = "both",
    workers: int = 4,
    ocr_backend: str = "rapidocr",
    no_vlm: bool = False
):
    opts = Options(
        workers=workers,
        ocr_backend=ocr_backend,
        vlm_backend="stub_vlm" if no_vlm else "vlm"
    )
    
    try:
        doc = parse(path, options=opts)
        
        if doc.errors and any(not e.recoverable for e in doc.errors):
            print("Fatal error occurred during parsing.")
            for e in doc.errors:
                print(f"[{e.code}] {e.message}")
            sys.exit(1)
            
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        base_name = Path(path).stem
        
        if format in ["json", "both"]:
            out_json = out / f"{base_name}.json"
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(doc.model_dump_json(indent=2))
                print(f"Exported JSON -> {out_json}")
                
        if format in ["md", "both"]:
            try:
                from parseanything.render.markdown import to_markdown
                md_text = to_markdown(doc)
                out_md = out / f"{base_name}.md"
                with open(out_md, "w", encoding="utf-8") as f:
                    f.write(md_text)
                print(f"Exported Markdown -> {out_md}")
            except ImportError:
                print("Markdown rendering not implemented yet.")
                
        print(f"Parse complete: {doc.stats.pages} pages, {doc.stats.blocks} blocks, {doc.stats.flagged_blocks} flagged.")
        print(f"Elapsed: {doc.stats.elapsed_s:.2f}s ({doc.stats.pages_per_sec:.2f} pages/sec)")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

try:
    import typer
    app = typer.Typer()
    @app.command("parse")
    def typer_parse_cmd(
        path: str = typer.Argument(..., help="Path to the document to parse"),
        out: Path = typer.Option(..., "--out", help="Output directory"),
        format: str = typer.Option("both", "--format", help="Output format: json|md|both"),
        workers: int = typer.Option(4, "--workers", help="Number of workers for parallel processing"),
        ocr_backend: str = typer.Option("rapidocr", "--ocr-backend", help="OCR backend name"),
        no_vlm: bool = typer.Option(False, "--no-vlm", help="Disable VLM usage")
    ):
        run_parse(path, out, format, workers, ocr_backend, no_vlm)
except ImportError:
    app = None

def main():
    if app is not None:
        app()
    else:
        import argparse
        parser = argparse.ArgumentParser(description="ParseAnything CLI")
        subparsers = parser.add_subparsers(dest="command")
        parse_p = subparsers.add_parser("parse", help="Parse document")
        parse_p.add_argument("path", help="Path to the document to parse")
        parse_p.add_argument("--out", "-o", required=True, help="Output directory")
        parse_p.add_argument("--format", "-f", default="both", choices=["json", "md", "both"], help="Output format")
        parse_p.add_argument("--workers", "-w", type=int, default=4, help="Workers")
        parse_p.add_argument("--ocr-backend", default="rapidocr", help="OCR backend")
        parse_p.add_argument("--no-vlm", action="store_true", help="Disable VLM")

        # Also support direct arguments without 'parse' subcommand
        parser.add_argument("path_direct", nargs="?", help="Direct path to document")
        parser.add_argument("--out", "-o", help="Output directory")
        parser.add_argument("--format", "-f", default="both", choices=["json", "md", "both"])
        parser.add_argument("--workers", "-w", type=int, default=4)
        parser.add_argument("--ocr-backend", default="rapidocr")
        parser.add_argument("--no-vlm", action="store_true")

        args = parser.parse_args()
        target_path = getattr(args, "path", None) or getattr(args, "path_direct", None)
        if not target_path or not args.out:
            parser.print_help()
            sys.exit(1)
        run_parse(target_path, Path(args.out), args.format, args.workers, args.ocr_backend, args.no_vlm)

if __name__ == "__main__":
    main()


# Handoff: Agent 1

## Status: Phases 0 & 1 Complete

**To: Agents 2, 3, and 4**

Agent 1 has completed the foundational framework and integration setup. The repository is ready for you to build your specific extraction pipelines.

### What has been implemented:
1. **Contract & Schema (`schema.py`, `interfaces.py`, `errors.py`):**
   - The data models (`Document`, `Page`, `Block`, `TableData`, `ChartData`, etc.) are frozen.
   - Core interfaces (`OCRBackend`, `LayoutBackend`, `VLMBackend`, `RegionExtractor`, `FormatParser`) are defined.
   - **Do not modify the schema** without logging it in `docs/REQUESTS.md`.
2. **Registry (`registry.py`):**
   - Use `register_ocr`, `register_layout`, `register_vlm`, `register_region_extractor`, and `register_format_parser` to register your implementations on import.
3. **Routing & Magic Bytes (`core/sniff.py`, `core/router.py`):**
   - Automatically detects format. PDFs and images route to the orchestrator; other files route to Agent 4's format parsers.
4. **Orchestrator & Parallelism (`core/orchestrator.py`, `core/parallel.py`):**
   - Multi-process page-level parallel processing. It expects Agent 2 to provide `render_page` and `classify_page`, then calls your registered backends and extractors per-region.
5. **Assembly (`core/assemble.py`):**
   - Reorders blocks and merges cross-page tables using Agent 2's `order_blocks` and Agent 3's `merge_cross_page_tables` (if available, otherwise uses fallbacks).
6. **Watchdog & Confidence (`core/watchdog.py`, `core/confidence.py`):**
   - The 55-second global timeout is active.
   - Confidence calculation is ready; use `combine()` to mix OCR and layout scores.
7. **CLI & API (`cli/main.py`, `api/main.py`):**
   - Fully functional Typer CLI and FastAPI upload points.
8. **Docker Support:**
   - Base `Dockerfile` and `docker-compose.yml` configured for a CPU-first local deployment.

## What you need to do:

### Agent 2 (PDF & OCR Pipeline)
- Build out `pdf/render.py` (with `pypdfium2`), `pdf/classify.py`, and `pdf/reading_order.py`.
- Implement `OCRBackend` using RapidOCR and/or Tesseract.
- Implement `LayoutBackend` (e.g., Docling, PP-DocLayout, or rule-based fallback).
- Build the `RegionExtractor` for text/title/list.
- Register your backends in `registry.py`!

### Agent 3 (Complex Blocks: Tables, Charts, Math)
- Implement `RegionExtractor` classes for `table`, `figure`, and `equation` labels.
- For tables: handle rowspan/colspan, grid lines, and cross-page merging (`tables/merge.py`).
- For charts: implement the VLM prompt-based extraction or OCR fallback (`charts/extract.py`).
- For math: reconstruct equations to LaTeX (`math/extract.py`).
- Register your extractors in `registry.py`!

### Agent 4 (Other Formats, Markdown, Eval & UI)
- Implement `FormatParser` classes for DOCX, XLSX, PPTX, legacy files, and EML.
- Register them using `register_format_parser`.
- Implement `to_markdown(doc)` in `render/markdown.py`.
- Provide the `/render/page` endpoint (see `docs/REQUESTS.md`) for the UI overlay.
- Expand `README.md` to include your eval results and demo UI instructions once complete.

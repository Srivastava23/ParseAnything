# ParseAnything: Multi-Agent Build Plan (DataQuest 3.0, DQCL)

## HOW TO USE THIS FILE (read first)

This file is given to 4 different AI coding agents (one per IDE), each working in the SAME git repo on a different part of the system.

The human will start the session by saying **"I AM AGENT N"** (N = 1, 2, 3 or 4).

1. Read **Part A** (shared context, schema, interfaces, rules). Every agent follows it.
2. Then read ONLY **your own section** in Part B (`AGENT N`). Do not do work from another agent's section.
3. If the human did not say which agent you are, ask: "Which agent am I (1-4)?" and wait.
4. Only edit files you own (listed in your section). If you need a change in a file you don't own, write it in `docs/REQUESTS.md` as `[from AGENT N -> AGENT M] <request>` and tell the human to relay it. Do not edit the file yourself.
5. When you finish a milestone, update `docs/HANDOFF_AGENT_N.md` with: what works, how to call it, known gaps.
6. Be pragmatic. This is a hackathon. Working and demoable beats perfect. Tag every task **[MUST]** or **[NICE]** and do all MUSTs first.

---

# PART A: SHARED CONTEXT

## A1. Project

**ParseAnything**: a high-fidelity universal document ingestion engine. One entry point converts PDFs (digital and scanned), images, DOCX, XLSX, PPTX, legacy Office files and emails into structured **JSON + Markdown**, with:

- typed semantic blocks (heading, paragraph, list, table, figure/chart, equation, header, footer, footnote)
- correct reading order (multi-column, sidebars, footnotes, headers and footers kept out of body)
- complex tables (merged cells, multi-row headers, tables merged across page breaks)
- chart data extracted as structured series (not placeholders)
- equations as LaTeX
- **bounding-box provenance** (page + bbox) and a **per-block confidence score**
- flagging low-confidence blocks (`flagged=true`) instead of hallucinating text
- structured error codes within 60 seconds for corrupt/unsupported files

Customer context: Cenizas Labs (private equity, banking, legal diligence). Missing a single line item or losing chart numbers is a critical failure.

**Judging has two halves, so build for both:**
1. Benchmark accuracy (text, tables, charts, math, reading order, bbox provenance).
2. Production practicality: high page throughput, sub-$10/1k pages API cost, **fully self-hosted commercial viability**, robust failure handling.

## A2. Hard constraints and decisions

- **Language:** Python 3.11. Package name: `parseanything`.
- **Self-hosted by default.** Core path must run with no cloud calls. Cloud services (Google Vision, Gemini) are allowed ONLY as optional plug-in backends behind interfaces and must be off by default.
- **Licenses:** prefer MIT/Apache/BSD. **Do NOT use PyMuPDF/fitz or AGPL models (e.g. Ultralytics YOLO weights)** in the core path. Use `pypdfium2` + `pdfplumber`. Each agent records every dependency and its license in `docs/LICENSES.md`.
- **CPU-first.** Assume no GPU. Anything GPU/VLM-heavy must degrade gracefully (fall back to a smaller model, an optional API backend, or `flagged` output).
- **Never raise out of the public entry point.** `parse()` always returns a `Document`; failures go into `Document.errors`.
- **60-second rule:** corrupt/unsupported files must return a structured error in under 60s. A global watchdog returns partial results plus a `TIMEOUT` error at ~55s.
- **No hallucination:** if an extractor is unsure, set low confidence and `flagged=true` with a `flag_reason`. Never invent text, numbers or table cells.

## A3. Repo layout and ownership

```
parseanything/
  schema.py              # AGENT 1  (contract; frozen after Phase 0)
  interfaces.py          # AGENT 1  (backend/extractor protocols)
  errors.py              # AGENT 1
  config.py              # AGENT 1
  registry.py            # AGENT 1
  core/                  # AGENT 1  (router, orchestrator, watchdog, confidence, parallel)
  api/  cli/             # AGENT 1
  pdf/                   # AGENT 2  (page classify, render, layout, reading order, hdr/ftr)
  ocr/                   # AGENT 2  (OCR backends)
  imageparse/            # AGENT 2  (image files -> same pipeline)
  tables/                # AGENT 3  (table extraction + cross-page merge)
  charts/                # AGENT 3  (chart -> data)
  math/                  # AGENT 3  (equation -> LaTeX)
  formats/               # AGENT 4  (docx, xlsx, pptx, legacy, email, csv, html/txt)
  render/                # AGENT 4  (JSON -> Markdown, HTML overlay data)
eval/                    # AGENT 4  (benchmark harness, metrics, datasets)
ui/                      # AGENT 4  (demo web UI with bbox overlay)
tests/fixtures/          # AGENT 4 creates; all may add files in their own subfolder
tests/<area>/            # each agent tests their own area
docs/                    # each agent owns HANDOFF_AGENT_N.md; shared: REQUESTS.md, LICENSES.md
Dockerfile docker-compose.yml pyproject.toml README.md
                         # AGENT 1 owns Docker/pyproject; AGENT 4 owns README.md
```

**Git rules:** each agent works on branch `agent-N/main-work`, commits small and often, and rebases on `main` before merging at checkpoints. Never force-push `main`. Never reformat files you don't own.

## A4. THE CONTRACT: schema (Agent 1 publishes in Phase 0; everyone codes against it)

Use Pydantic v2. Coordinates: **PDF points, origin top-left, y grows downward**, plus page width and height stored on `Page`. Confidence is a float 0.0-1.0.

```python
# parseanything/schema.py  (target shape; Agent 1 finalizes)
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field

class BlockType(str, Enum):
    HEADING="heading"; PARAGRAPH="paragraph"; LIST="list"; TABLE="table"
    FIGURE="figure"; CHART="chart"; EQUATION="equation"; CAPTION="caption"
    HEADER="header"; FOOTER="footer"; FOOTNOTE="footnote"; CODE="code"; OTHER="other"

class BBox(BaseModel):
    x0: float; y0: float; x1: float; y1: float

class TableCell(BaseModel):
    row: int; col: int; rowspan: int = 1; colspan: int = 1
    text: str; is_header: bool = False

class TableData(BaseModel):
    n_rows: int; n_cols: int
    cells: list[TableCell]
    header_rows: int = 0
    markdown: Optional[str] = None      # lossy fallback (spans flattened)
    html: Optional[str] = None          # lossless (colspan/rowspan)
    pages: list[int] = []               # >1 page if merged across page break

class Point(BaseModel):
    x: float | str; y: float

class Series(BaseModel):
    name: str; points: list[Point]

class ChartData(BaseModel):
    chart_type: str                      # bar|line|pie|scatter|area|other
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    series: list[Series] = []
    data_table_markdown: Optional[str] = None
    caption: Optional[str] = None
    values_estimated: bool = True        # True if read off visually, not from labels

class Block(BaseModel):
    id: str                              # stable, e.g. "p3_b12"
    type: BlockType
    page: int                            # 1-indexed (slide / sheet index for non-paged)
    bbox: Optional[BBox] = None          # None for formats with no geometry
    locator: Optional[str] = None        # e.g. "docx:para:12", "xlsx:Sheet1!A1:D10"
    content: str = ""                    # text / markdown / LaTeX (for equations)
    level: Optional[int] = None          # heading level 1-6
    table: Optional[TableData] = None
    chart: Optional[ChartData] = None
    latex: Optional[str] = None
    reading_order: int = 0               # global order across the document
    confidence: float = 1.0
    flagged: bool = False
    flag_reason: Optional[str] = None
    source_extractor: str = ""           # e.g. "pdfplumber", "rapidocr", "tableformer"
    meta: dict = {}

class Page(BaseModel):
    number: int; width: float; height: float
    kind: Literal["digital","scanned","mixed","image","virtual"] = "digital"
    blocks: list[Block] = []

class ErrorCode(str, Enum):
    CORRUPT_FILE="CORRUPT_FILE"; UNSUPPORTED_FORMAT="UNSUPPORTED_FORMAT"
    PASSWORD_PROTECTED="PASSWORD_PROTECTED"; EMPTY_FILE="EMPTY_FILE"
    FILE_NOT_FOUND="FILE_NOT_FOUND"; TIMEOUT="TIMEOUT"
    EXTRACTOR_FAILED="EXTRACTOR_FAILED"  # partial failure, recoverable
    BACKEND_UNAVAILABLE="BACKEND_UNAVAILABLE"; INTERNAL_ERROR="INTERNAL_ERROR"

class ParseError(BaseModel):
    code: ErrorCode; message: str
    stage: Optional[str] = None; page: Optional[int] = None
    recoverable: bool = False

class DocStats(BaseModel):
    pages: int = 0; blocks: int = 0; flagged_blocks: int = 0
    elapsed_s: float = 0.0; pages_per_sec: float = 0.0
    est_cost_usd: float = 0.0            # 0.0 for self-hosted path

class Document(BaseModel):
    source: str; format: str             # detected via magic bytes
    pages: list[Page] = []
    errors: list[ParseError] = []
    stats: DocStats = DocStats()
    meta: dict = {}
```

## A5. THE CONTRACT: interfaces (Agent 1 publishes in `interfaces.py`)

```python
# Shapes (Agent 1 finalizes exact signatures; everyone codes to these)
class Region(BaseModel):            # output of layout detection
    bbox: BBox; label: str          # text|title|table|figure|equation|header|footer|footnote|list|caption
    score: float

class PageContext:                  # handed to extractors
    page_number: int; width: float; height: float
    image: "PIL.Image"              # rendered page (default 200 DPI); scale = dpi/72
    scale: float
    pdf_page: object | None         # pypdfium2/pdfplumber handle if digital
    kind: str                       # digital|scanned|mixed|image

class OCRLine(BaseModel): text: str; bbox: BBox; confidence: float

class OCRBackend(Protocol):  name: str; def ocr(self, image, bbox: BBox|None=None) -> list[OCRLine]
class LayoutBackend(Protocol): name: str; def detect(self, ctx: PageContext) -> list[Region]
class VLMBackend(Protocol):  name: str; def describe_chart(self, image) -> ChartData; def read_equation(self, image) -> str
class RegionExtractor(Protocol):   # tables / charts / math / text extractors
    name: str; handles: set[str]    # which Region.labels it accepts
    def extract(self, ctx: PageContext, region: Region) -> list[Block]
class FormatParser(Protocol):      # non-PDF formats
    name: str; extensions: set[str]; mime: set[str]
    def parse(self, path: str, opts: "Options") -> Document
```

`registry.py` provides `register_ocr / register_layout / register_vlm / register_region_extractor / register_format_parser` plus lookups. Backends and extractors self-register on import, and Agent 1's orchestrator discovers them. **Public entry point:** `parseanything.parse(path_or_bytes, options=None) -> Document` (never raises).

## A6. Pipeline (what the system does)

1. **Detect & Route (Agent 1 router + Agent 2 page classifier):** sniff format by magic bytes (not extension). For PDF pages decide `digital | scanned | mixed`. Run layout detection to label regions. Route each region to the specialist extractor.
2. **Extract & Assemble (Agents 2 and 3 produce blocks; Agent 1 assembles):** typed blocks, global reading order, header/footer separation, cross-page table merge, bbox + confidence on everything.
3. **Flag & Fail Safe (Agent 1):** confidence scoring, `flagged` threshold (default 0.6), structured errors, 60s watchdog.
4. **Render (Agent 4):** Markdown generated FROM the JSON, with block ids as HTML comments (`<!-- p3_b12 conf=0.91 -->`) for traceability.

## A7. Milestones (≈24h plan; scale if you have less)

| Phase | Time | Goal |
|---|---|---|
| **0: Contract** | 0-1h | Agent 1 pushes `schema.py`, `interfaces.py`, `registry.py`, `errors.py`, stub backends, and a working `parse()` that returns an empty-but-valid Document. **Agents 2-4 may start only after this lands** (until then, read your section and set up env/dependencies/fixtures). |
| **1: Build** | 1-12h | Each agent builds MUSTs against the contract using stubs for others' work. |
| **2: Integrate** | 12-18h | Merge to `main`; end-to-end runs on the fixture set; fix interface mismatches via `docs/REQUESTS.md`. |
| **3: Harden + polish** | 18-22h | Benchmarks, confidence tuning, failure handling, Docker, UI polish, README, demo script. |
| **4: Freeze** | last 2h | No new features. Bugfix and rehearsal only. |

## A8. Definition of done (project-level)

- `python -m parseanything.cli parse file.pdf --out out/` produces `out/file.json` and `out/file.md`.
- `docker compose up` exposes `POST /parse` and `GET /health`.
- Works on: digital PDF, scanned PDF, photo of a page, DOCX, XLSX, PPTX, legacy `.doc/.xls/.ppt`, `.eml/.msg`.
- Corrupt, encrypted and unsupported files return structured errors in <60s.
- Eval table in README comparing against a baseline (plain `pdfplumber` text dump).

---

# PART B: AGENT SECTIONS

---

## AGENT 1: Core platform, contract, orchestration, API, ops

**You are the integrator. The team is blocked on your Phase 0, so ship it fast and keep it frozen afterward.**

**You own:** `schema.py`, `interfaces.py`, `errors.py`, `config.py`, `registry.py`, `core/`, `api/`, `cli/`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, CI config, `tests/core/`.

### Tasks

**Phase 0 (≤1h, top priority) [MUST]**
- Create repo skeleton per A3, `pyproject.toml` (deps pinned loosely), and the package structure.
- Implement `schema.py` and `interfaces.py` exactly per A4/A5 (adjust only for correctness; announce any change in `docs/REQUESTS.md`).
- Implement `registry.py` and `errors.py`.
- Implement stub backends: `StubOCR`, `StubLayout`, `StubVLM`, so others can run end to end.
- Implement `parse()` that returns a valid empty `Document` for any input. Push to `main`. Tell the human: "Phase 0 is live."

**Phase 1 [MUST]**
1. `core/sniff.py`: magic-byte format detection (PDF, PNG/JPG/TIFF/BMP/WEBP, ZIP-based OOXML -> docx/xlsx/pptx by inspecting `[Content_Types].xml`/folders, OLE2 -> doc/xls/ppt/msg, RFC822 -> eml, CSV/TXT/HTML heuristics). Extension is only a tie-breaker.
2. `core/router.py`: `format -> parser`. PDFs and images go to Agent 2's pipeline; the other formats go to Agent 4's `FormatParser`s through the registry.
3. `core/orchestrator.py`: for paged inputs: for each page (a) build `PageContext`, (b) layout detect, (c) dispatch regions to `RegionExtractor`s by label, (d) collect blocks. Support **page-level parallelism** via `ProcessPoolExecutor` (`core/parallel.py`) with a configurable worker count. Isolate per-page failures: one bad page gives `EXTRACTOR_FAILED` with `page=N`, and the rest continue.
4. `core/assemble.py`: calls Agent 2's `order_blocks()` for reading order and Agent 3's `merge_cross_page_tables()` (both via registry hooks), assigns stable ids (`p{page}_b{idx}`), sets global `reading_order`, and fills `DocStats`.
5. `core/watchdog.py`: global ~55s budget. On expiry, return partial `Document` with `TIMEOUT` (recoverable=True). Per-file pre-checks (empty file, unreadable, encrypted PDF -> `PASSWORD_PROTECTED`, unknown magic -> `UNSUPPORTED_FORMAT`) must return in a couple of seconds.
6. `core/confidence.py`: `combine(ocr_conf=None, layout_score=None, heuristics=...) -> float` and `apply_flagging(block, threshold)`. Heuristics: very short text with low OCR confidence, non-dictionary garbage ratio, table with empty-cell ratio > X, chart with `values_estimated`. Document the formula in the docstring.
7. `cli/`: Typer app: `parse <path> --out DIR --format json|md|both --workers N --ocr-backend NAME --no-vlm`. Exit code non-zero on fatal errors; print `DocStats`.
8. `api/`: FastAPI: `POST /parse` (multipart upload, returns Document JSON; `?format=md` returns Markdown), `GET /health`, `GET /backends` (lists registered backends). Request size limit and a per-request timeout matching the watchdog.
9. `Dockerfile` + `docker-compose.yml`: CPU image, models baked or downloaded on first run to a mounted volume, healthcheck. Include LibreOffice (for legacy formats, Agent 4) and Tesseract if Agent 2 uses it.
10. `config.py`: env/CLI-driven `Options` (dpi, workers, confidence threshold, enabled backends, cloud fallbacks default OFF).

**Phase 2 [MUST]**
- Own integration: merge branches, run the fixture set end to end, triage `docs/REQUESTS.md`, keep `main` green.
- Cost report: `est_cost_usd = 0` for self-hosted path; if a cloud backend is enabled, compute estimated $/1k pages from a config table of per-call prices (mark the figures as configurable and unverified).

**[NICE]**
- Batch endpoint `POST /parse/batch` and async job queue.
- Prometheus-style `/metrics`; structured JSON logging with a request id.
- Optional GPU compose profile.
- Content-hash result cache.

**Done when:** every error code in A4 can be triggered by a test file and returns in <60s; `docker compose up` serves `/parse`; one bad page never kills a document; a pages/sec number is printed for a 20-page PDF.

---

## AGENT 2: PDF pipeline, OCR, layout, reading order

**You own:** `pdf/`, `ocr/`, `imageparse/`, `tests/pdf/`, `tests/ocr/`.

**Reference from the team's earlier project (reuse the idea, not the code or cloud dependency):** previously every PDF page was rendered at 300 DPI and sent to Google Cloud Vision for OCR. Keep "render page to image -> OCR" for scans, but (1) use `pypdfium2`, not PyMuPDF (AGPL), (2) only OCR when needed, (3) keep per-word bboxes and confidence instead of flat text, (4) Google Vision becomes an OPTIONAL `OCRBackend`.

### Tasks

**Phase 1 [MUST]**
1. `pdf/render.py`: `render_page(pdf, page_no, dpi) -> PIL.Image` with `pypdfium2`; build `PageContext` (width/height in points, scale). Handle rotated pages and page boxes.
2. `pdf/classify.py`: classify each page as `digital | scanned | mixed` using the char count from `pdfplumber`/pdfium text layer, image-area coverage, and garbage-text check (text layer that is nonsense, e.g. broken font encoding, should be treated as scanned). Output the kind plus the regions needing OCR. Digital pages must NOT go through OCR (speed + accuracy).
3. `ocr/rapidocr_backend.py` (default) and `ocr/tesseract_backend.py` (fallback), both implementing `OCRBackend`, returning `OCRLine` with bboxes converted to PDF points and per-line confidence. Auto-select via registry; lazy-load models. Optional `ocr/google_vision_backend.py` (OFF by default; adapt the earlier Vision `document_text_detection` code to emit `OCRLine`s).
4. `pdf/layout.py`: `LayoutBackend` using a permissively licensed layout model (try Docling's layout model or PP-DocLayout via ONNX; **check the license before adding**). Provide a **rule-based fallback** (`HeuristicLayout`: ruled-line/whitespace analysis, font-size based headings, table detection via `pdfplumber` lines) so the pipeline works even when no model is available. Labels: text, title, list, table, figure, equation, header, footer, footnote, caption.
5. `pdf/text_blocks.py`: `RegionExtractor` for `text/title/list/caption/footnote` regions. For digital pages, pull chars/words from the text layer inside the region (keep font size for heading levels). For scanned regions, call OCR on the crop. Merge lines into paragraphs; detect lists (bullets/numbering). Heading level from relative font size/weight (digital) or layout label plus size (scanned).
6. `pdf/reading_order.py`: `order_blocks(blocks, page) -> list[Block]` implementing recursive **XY-cut** with column detection (handle 1, 2, 3 columns, full-width headings spanning columns, sidebars). Tag `header/footer` blocks (repeated text near top/bottom edges across pages, page numbers) so they are excluded from the body flow but kept in JSON. Footnotes go after the body of their page.
7. `imageparse/`: image files (PNG/JPG/TIFF/etc.) go through the same pipeline as a single-page "scanned" doc. Add deskew/denoise/contrast preprocessing (`opencv-python-headless`/PIL) and EXIF rotation. Multi-page TIFF = multiple pages.
8. Per-block confidence: OCR mean confidence x layout score for scanned; ~0.95-0.99 for clean digital text. Pass `ocr_conf` and `layout_score` through to Agent 1's `confidence.combine`.
9. Robustness: password-protected -> raise a typed internal exception mapped to `PASSWORD_PROTECTED`; broken PDFs -> try `pdfium` repair/fallback before `CORRUPT_FILE`; huge pages -> cap DPI.

**[NICE]**
- Multi-language OCR (hi/ta, since the team is in Chennai: good demo).
- Handwriting/low-quality photo handling with a second-pass higher-DPI OCR on low-confidence regions.
- Rotated-text/vertical-text blocks.
- Table-of-contents and PDF bookmark-derived heading hierarchy.
- Caching of rendered pages.

**Interfaces you provide to others:** `PageContext` builder, `LayoutBackend` regions (Agent 3 consumes `table/figure/equation` regions), `order_blocks()`, `OCRBackend` (Agent 3 may call it for scanned table cells, so keep `ocr(image, bbox)` crop-friendly).

**Done when:** a 2-column digital paper reads in the right order; a scanned PDF and a phone photo of a page produce text with bboxes and confidences; headers/footers/page numbers are tagged and excluded from body flow; a 20-page digital PDF parses at multi-page/second speed on CPU (report your number in `HANDOFF_AGENT_2.md`).

---

## AGENT 3: Tables, charts, equations

**You own:** `tables/`, `charts/`, `math/`, `tests/tables/`, `tests/charts/`, `tests/math/`.

### Tasks

**Phase 1 [MUST]**
1. `tables/extract.py`: `RegionExtractor` for `table` regions. Strategy cascade:
   a. **Digital PDF with ruled lines**: `pdfplumber` lines/rects strategy -> cells with correct row/col and **rowspan/colspan** (detect merged cells from missing internal edges).
   b. **Digital without lines**: text-alignment/whitespace strategy.
   c. **Scanned / image tables**: use a table-structure model (Docling TableFormer or equivalent, **check license**) if available; otherwise OCR (Agent 2's `OCRBackend`, crop-level) and reconstruct the grid by clustering word boxes into rows/columns.
   Emit `TableData` with `cells`, `header_rows` (detect multi-row headers), `markdown`, and lossless `html` (colspan/rowspan). Block `content` = the Markdown version; `bbox` = table bbox; confidence = structure consistency (rectangular, low empty ratio) x extractor confidence.
2. `tables/merge.py`: `merge_cross_page_tables(blocks_by_page) -> blocks`: merge a table at the bottom of page N with one at the top of page N+1 when column counts/x-positions match, and handle repeated header rows on the continuation page (drop the duplicate header, don't duplicate rows). Record `TableData.pages=[N, N+1]` and keep per-page bboxes in `meta["page_bboxes"]`. Register it as the hook Agent 1's `assemble.py` calls.
3. `tables/numbers.py`: financial hygiene: keep cell text exactly as printed (parentheses negatives, currency, %, footnote markers) and never "fix" numbers. Provide a validator that flags cells where the OCR'd numeric text looks suspicious (e.g. `O` vs `0`) and lowers confidence.
4. `charts/extract.py`: `RegionExtractor` for `figure` regions. First classify: chart vs photo/diagram/logo. For charts, produce `ChartData`:
   - **Digital PDFs**: pull text labels/tick values/legend text from the text layer inside the region (these are the true numbers).
   - **Via `VLMBackend.describe_chart(image)`**: implement a local VLM backend (`charts/vlm_local.py`: e.g. Qwen2.5-VL-3B/7B via Ollama or `llama.cpp` server, configurable URL; must fail gracefully if unavailable) and an OPTIONAL cloud backend (`charts/vlm_gemini.py`, OFF by default, behind an env var; reuse the earlier project's "force JSON output" pattern and verify the current model name). Prompt the VLM to return strict JSON matching `ChartData`; validate with Pydantic; retry once on invalid JSON.
   - **No VLM available fallback (must work offline)**: OCR the chart region and return `ChartData` with the labels/title/legend and any printed data labels, `values_estimated=True`, `flagged=True`, `flag_reason="chart values not extracted (no VLM)"`. Never fabricate series values.
   - Cross-check: if data labels printed on the chart disagree with VLM values, prefer the printed labels and lower confidence.
   - Output `Block(type=CHART, chart=ChartData, content=<data table as markdown + caption>)`. Figures that aren't charts become `FIGURE` blocks with a caption/alt description (VLM if available, else nearby caption text).
5. `math/extract.py`: `RegionExtractor` for `equation` regions: image -> LaTeX using `pix2tex` (LaTeX-OCR) or a PP-FormulaNet ONNX model (**check license**). Output `Block(type=EQUATION, latex=..., content="$$...$$")`. Sanity-check LaTeX (balanced braces, parseable with `latex2mathml`/`sympy.parsing.latex` if present); flag on failure. For digital PDFs with a math-font text layer, try a text-layer-based reconstruction first.
6. All extractors must handle missing models without crashing: return flagged placeholder blocks with `BACKEND_UNAVAILABLE` info in `meta`.

**[NICE]**
- Detect inline math inside paragraphs and convert to `$...$`.
- Table-of-numbers sanity checks (e.g. totals row = sum of rows -> confidence boost, mismatch -> flag with reason). A strong demo for the finance and legal story.
- Chart-type-specific extraction, e.g. pie percentages, stacked bars.
- Nested/rotated table support.

**Interfaces you consume:** `Region`s from Agent 2's layout and `OCRBackend`. **You provide:** `RegionExtractor`s registered for labels `table`, `figure`, `equation`, plus `merge_cross_page_tables()`.

**Done when:** a financial PDF with merged-cell, multi-row-header tables yields correct `rowspan/colspan` HTML; a table split across two pages becomes ONE block with no duplicated header; a bar chart yields a data table (or a clearly flagged partial when no VLM); a displayed equation yields valid LaTeX.

---

## AGENT 4: Other formats, rendering, evaluation, demo UI

**You own:** `formats/`, `render/`, `eval/`, `ui/`, `tests/fixtures/`, `tests/formats/`, `tests/render/`, `README.md`.

### Tasks

**Phase 1 [MUST]**
1. `formats/docx.py` (`python-docx`): walk the body in true document order (paragraphs AND tables interleaved; iterate the XML body, not `doc.paragraphs`). Map styles to headings (`Heading 1..6`, `Title`), lists (numbering), tables (merged cells via `gridSpan`/`vMerge` -> `TableData` with spans), headers/footers, footnotes if accessible, embedded images -> `FIGURE` blocks (optionally send to the chart pipeline). `locator="docx:para:N"` / `"docx:table:N"`; `bbox=None`.
2. `formats/xlsx.py` (`openpyxl`, plus `pandas` for CSV/TSV): each sheet = a "page"; detect table regions (contiguous data blocks, header row guess, merged cells), emit `TableData` and a block per region; sheet title as heading; also handle hidden sheets/rows (mark in `meta`), and charts embedded in sheets (extract series refs from the chart XML into `ChartData` when possible: real data, high confidence). `locator="xlsx:Sheet1!A1:D10"`. Evaluate formulas by cached values (`data_only=True`) and note when none are cached.
3. `formats/pptx.py` (`python-pptx`): each slide = a page; title -> heading, text frames -> paragraph/list (preserve levels), tables, speaker notes (`meta` or separate `FOOTNOTE`-type block), pictures/charts (native pptx charts expose real series data -> `ChartData` with high confidence). Use shape position as `bbox` (EMU -> points) so overlay still works.
4. `formats/legacy.py`: `.doc/.xls/.ppt` (+ `.rtf`, `.odt` etc.): convert with **LibreOffice headless** (`soffice --headless --convert-to docx|xlsx|pptx`) in a temp dir with a timeout (<=30s) and then delegate to the modern parser. Make sure that conversion hangs/crashes map to `CORRUPT_FILE`/`TIMEOUT`, never a hang. Use a unique `-env:UserInstallation` profile dir per call so parallel runs don't collide.
5. `formats/email.py`: `.eml` (stdlib `email` + `policy.default`) and `.msg` (`extract-msg`): headers (from/to/date/subject) as a structured block, body (prefer plain text; fall back to HTML->text), and **attachments parsed recursively** through `parseanything.parse` (cap recursion depth, e.g. 3), with the attachment name as a heading. Strip quoted reply chains into flagged/collapsed blocks (`meta["quoted"]=True`).
6. `formats/misc.py`: `.txt`, `.md`, `.html` (BeautifulSoup: headings/lists/tables), `.csv/.tsv`.
7. `render/markdown.py`: `to_markdown(doc, include_ids=True) -> str` from the JSON: headings with `#` levels by `level`, lists, tables as GFM (fallback to inline HTML when spans exist), equations as `$$`, charts as a data table plus caption, header/footer blocks omitted from body (optionally appended in an appendix), flagged blocks marked (`> ⚠️ low confidence: reason`), and an HTML comment per block with id/page/confidence. Order strictly by `reading_order`.
8. `tests/fixtures/` + `eval/dataset/`: build a small dev set (~10-15 files) covering: 2-column digital PDF, scanned PDF, phone-photo page, financial statement with merged-cell tables, table split across pages, PDF with a bar/line chart, PDF with equations, DOCX with tables, XLSX, PPTX with chart, legacy `.doc`/`.xls`, `.eml` with attachment, corrupt PDF, password-protected PDF, empty file. Use freely licensed or self-generated files only. For a few, create small hand-written ground truth (JSON/Markdown).
9. `eval/`: harness `python -m eval.run --data eval/dataset --out eval/results`:
   - **Text/OCR:** normalized edit distance / CER-WER vs ground truth.
   - **Reading order:** order-correctness (e.g. Kendall tau / normalized edit distance on block sequence).
   - **Tables:** TEDS-style tree-edit similarity (or simpler cell-level F1 if time is short).
   - **Charts:** series/value match rate within tolerance.
   - **Equations:** normalized LaTeX string similarity.
   - **Provenance:** share of blocks with valid bbox in page bounds; IoU on labeled boxes where available.
   - **Failure handling:** each bad-file fixture returns the expected `ErrorCode` in <60s.
   - **Throughput + cost:** pages/sec, and $/1k pages from `DocStats`.
   - **Baseline:** plain `pdfplumber.extract_text()` dump scored with the same metrics. Output a Markdown comparison table, which goes straight into the README and demo.
10. `ui/`: a small demo web app (single-page HTML+JS served by Agent 1's FastAPI as static files, or standalone Vite/React; keep it light): upload a file, show the page image with **colored bbox overlays by block type**, hover/click shows block id, type, confidence, and extracted content; side-by-side Markdown preview and a JSON tab; flagged blocks highlighted; error display for bad files. Needs `/parse` returning page images or a `/render/page` endpoint (request it from Agent 1 via `docs/REQUESTS.md` early).
11. `README.md`: pitch (problem -> approach), architecture diagram (Mermaid), quick start (CLI, Docker, API), supported formats, output schema summary, eval results table, cost/throughput numbers, limitations, license table (from `docs/LICENSES.md`), and a demo script (2-3 minute walkthrough in order: digital table -> scanned page -> chart -> equation -> email attachment -> corrupt file).

**[NICE]**
- Route DOCX/PPTX through LibreOffice -> PDF -> PDF pipeline as an optional mode (`--geometry`) to obtain real bboxes for office files.
- Eval score badges, a CI job that runs the eval, an HTML report of diffs.
- A second UI tab comparing ParseAnything vs the baseline.
- Export to `.jsonl` chunks for RAG (block-level chunks with provenance), which supports the "AI assistants" story.

**Done when:** all MUST formats parse to valid `Document`s; `to_markdown` output reads cleanly on every fixture; `eval.run` prints the comparison table; the UI overlays boxes on at least the PDF fixtures; README has a runnable quick start.

---

## B-final: Cross-agent checklist (Agent 1 runs this at Phase 2)

- [ ] `parse()` never raises; every error path returns a coded `ParseError`.
- [ ] Every PDF/image block has a bbox inside page bounds, a confidence, and `source_extractor`.
- [ ] Reading order verified on a 2-column fixture.
- [ ] Cross-page table merged on the split-table fixture.
- [ ] Flagged blocks carry `flag_reason`; nothing hallucinated when a backend is missing.
- [ ] Core path makes zero network calls (verify with network disabled).
- [ ] `docs/LICENSES.md` is complete with no AGPL in the core path.
- [ ] Docker image builds and `/parse` works from a clean checkout.
- [ ] README eval table and demo script are final.

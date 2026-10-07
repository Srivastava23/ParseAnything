# ParseAnything

**ParseAnything** is a high-fidelity universal document ingestion engine. It serves as a unified entry point to convert PDFs (digital and scanned), images, DOCX, XLSX, PPTX, legacy Office files, and emails into structured **JSON + Markdown**.

## Features
- **Typed Semantic Blocks:** Extracts headings, paragraphs, lists, tables, figures, charts, and equations.
- **Reading Order:** Maintains correct reading order, even in multi-column layouts, sidebars, footnotes, and headers/footers.
- **Complex Tables:** Reconstructs merged cells, multi-row headers, and tables merged across page breaks.
- **Provenance & Confidence:** Provides bounding-box provenance (page + bbox) and per-block confidence scores.
- **Fail-Safe Mechanism:** Falls back to `flagged=true` instead of hallucinating text, with a strict 60-second watchdog.

## Architecture & Setup
- **Core Platform:** Agent 1 has laid down the pipeline contract, registry, CLI, and API (`/parse`).
- **PDF Pipeline:** Agent 2 handles rendering, OCR, layout detection, and reading order mapping.
- **Table/Chart/Math Extractors:** Agent 3 handles complex data block extraction.
  - *Tables*: Extracts grid cells, handles `rowspan`/`colspan`, and merges tables across pages. Validates financial OCR numbers.
  - *Charts*: Leverages local VLMs or Gemini to extract raw data from charts.
  - *Math*: Uses `pix2tex` to convert images of equations into precise LaTeX.
- **Format Parsers & Renderers:** Agent 4 handles DOCX, PPTX, XLSX, legacy formats, and the UI demo.

### Quick Start
```bash
# Clone the repository
git clone https://github.com/Srivastava23/ParseAnything.git
cd ParseAnything

# Install dependencies
pip install .

# Run the API locally
docker-compose up
# API will be available at http://localhost:8000
```

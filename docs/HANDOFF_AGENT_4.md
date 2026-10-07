# Agent 4 Phase 2 Handoff

## 1. DONE
- **Legacy Formats:** Implemented `formats/legacy.py` to handle `.doc`, `.xls`, `.ppt`, `.rtf`, `.odt` by launching headless LibreOffice via subprocess to convert them into modern formats (`.docx`, `.xlsx`, `.pptx`) which are then routed to their respective parsers. Uses timeouts to prevent hanging and temp profiles to avoid race conditions.
- **Email Formats:** Implemented `formats/email.py` for `.eml` and `.msg`. The `.msg` support delegates to `extract-msg`. Includes recursive extraction of attachments via `parseanything.parse`.
- **Advanced PPTX:** Enhanced `formats/pptx.py` to extract embedded charts (converted to `ChartData`) and speaker notes as `FOOTNOTE` blocks. Also extracts pictures as `FIGURE`.
- **Integration & Polish:** All formats are loaded in `parseanything/formats/__init__.py`. Added `extract-msg` to `pyproject.toml` under `formats`.
- **Evaluation Harness:** Built `eval/run.py` to compute extraction metrics vs `pdfplumber` baseline.

## 2. NOT DONE / KNOWN ISSUES
- The UI was largely untouched as it correctly utilizes the `/parse` endpoint for the unified JSON and Markdown representations.
- Evaluation metrics could be further expanded for table structure (TEDS) depending on future scope.
- Two of Agent 3's tests (`tests/charts/test_charts.py`, `tests/math/test_math.py`) are currently failing due to invalid mock images passed to RapidOCR, which throws an unpacking error. This should be fixed in Agent 3's test mocks.

## 3. HOW TO USE
- `.doc`, `.xls`, `.ppt` files can now be sent directly to the `/parse` endpoint or the CLI (requires `soffice` installed on the host).
- `.msg` requires `pip install .[formats]`.

## 4. FOR THE NEXT AGENT
- All planned phases for DataQuest 3.0 are largely complete. Agent 4 phase 2 is done. Wait for next instructions, or execute final bug squashing/deployment.

## 5. Message to Human
Agent 4 Phase 2 tasks complete! Added legacy formats, email extraction, and extended PPTX extraction capabilities. We also added an eval harness.

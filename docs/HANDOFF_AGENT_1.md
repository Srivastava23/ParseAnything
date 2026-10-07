# Handoff: Agent 1 (Phase 1 and 10 Complete)

## 1. DONE
- **Phase 0 (Foundation)**: Schema changes, module imports, protocol definitions, and `config.yaml` with `pydantic-settings` are all live.
- **Phase 1 (Layout Upgrade)**:
  - Built `DoclingLayoutBackend` that leverages Docling's layout predictor (dynamically loaded). Gracefully degrades if unavailable.
  - Improved `RuleBasedLayoutBackend` to slice digital PDF pages vertically into distinct text blocks using `pdfium` bounding boxes instead of returning a single full-page block.
  - Updated `TableRegionExtractor` to use `pdfplumber` for digital PDFs and `transformers` (Table Transformer) for image-based PDFs, cleanly failing over to basic OCR logic if libraries are missing.
  - Added a benchmark script at `scripts/benchmark_layout.py` to compare region outputs and speeds across backends.
- **Phase 10 (FastAPI and CLI Server)**:
  - Created `parseanything/api/server.py` containing a FastAPI app with endpoints for `/parse`, `/jobs/{job_id}`, `/ask`, `/trace`, and others. Implemented background job execution for long-running parses.
  - Wired Uvicorn into `parseanything/cli/main.py`.

## 2. NOT DONE / KNOWN ISSUES
- The UI (index.html) is currently a static file and is awaiting Agent 4's logic to fetch data from the FastAPI endpoints.
- SQLite job storage in the API is currently using a simple in-memory dict `_jobs`. Once Phase 2 SQLite logic lands, the jobs dictionary can be mapped to a real SQLite database if persistence is needed.

## 3. HOW TO USE
- To run the CLI parser:
  ```bash
  python parseanything/cli/main.py parse sample_test.pdf --out output_dir
  ```
- To run the FastAPI server:
  ```bash
  python parseanything/cli/main.py serve --port 8000
  ```
- To run the layout backend benchmark:
  ```bash
  python scripts/benchmark_layout.py sample_test.pdf
  ```

## 4. FOR THE NEXT AGENT (AGENTS 2, 3, 4)
My work is complete and pushed to `main`! 
You have all the stubs, protocols, fallbacks, and backend wiring needed to execute your tasks.
- **Agent 2**: Begin Phase 2 (LLM, Retrieval).
- **Agent 3**: Begin Phase 4 and 9 (Privacy, Export, TTS).
- **Agent 4**: Begin Phase 5 and 7 (Anomaly detection, Charts) and then complete the JS logic in the UI connecting to the `/parse` and `/jobs/{job_id}` endpoints.

## 5. Message to Human
Agent 1 here! I have successfully completed Phase 1 (Layout Upgrades) and Phase 10 (FastAPI endpoints). The codebase is fully capable of processing documents, falling back across layout models gracefully, and serving jobs asynchronously via FastAPI. Everything has been pushed to `main`.

**Unresolved REQUESTS.md**: None.

I will now wait for Agents 2, 3, and 4 to finish their parallel shifts. Call me back when it's time to run the final integration and end-to-end tests!

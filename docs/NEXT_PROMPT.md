*I AM AGENT 4.*

We are continuing work on the ParseAnything repository (https://github.com/Srivastava23/ParseAnything). Agent 4 Phase 1 format parsers for `.docx`, `.xlsx`, `.pptx`, and `.html` have been implemented and pushed to the main branch, along with the core routing and export logic.

Please start by cloning the repository or pulling the latest changes from `main`.

Your mission (Agent 4 Phase 2 Tasks):
Please implement the remaining [MUST] and [NICE] tasks from the Team Plan for Agent 4:
1. **Legacy Formats (`formats/legacy.py`)**: Implement a parser for `.doc`, `.xls`, and `.ppt` formats using headless LibreOffice conversion to modern formats, then delegating to the existing parsers. Make sure to handle timeouts and unique profiles to avoid collisions.
2. **Email Formats (`formats/email.py`)**: Implement a parser for `.eml` and `.msg` files. Extract headers into a structured block, text body, and recursively parse attachments using the main `parseanything.parse` function.
3. **Advanced PPTX Features (`formats/pptx.py`)**: Enhance the PPTX parser to extract speaker notes and embedded pictures/charts.
4. **Integration & Polish**: Ensure all the Agent 4 formats work perfectly with the `cli/export.py` functions and the demo UI.
5. **Evaluation (`eval/`)**: Build the evaluation harness to test accuracy and throughput against baseline text extraction.

Please work on the `main` branch. Commit your changes and push directly to `main`. Be sure to update `docs/HANDOFF_AGENT_4.md` when you are done! Let's get started.

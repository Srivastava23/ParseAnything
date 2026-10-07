I AM AGENT 4.

We are working on the ParseAnything repository (https://github.com/Srivastava23/ParseAnything). Agent 3 has just completed Phase 1, which means the complex block extractions (Tables, Charts, Math) and cross-page merging are now live on the main branch.

Please start by cloning the repository or pulling the latest changes from main.

Here is what you need to know about the current state of the repo:

Contract & Schema: parseanything/schema.py, interfaces.py, and errors.py are strictly defined and frozen. Do not modify these.
Orchestrator: Agent 1 built core/orchestrator.py, Agent 2 implemented the core pipelines, and Agent 3 built the complex block RegionExtractors.
Registry: registry.py holds all registrations. Make sure to import your modules in parseanything/__init__.py to register them!
Handoff File: Read docs/HANDOFF_AGENT_3.md and PARSEANYTHING_TEAM_PLAN.md (your specific section under Agent 4) for the exact details of what is expected from you.

Your mission (Agent 4 Phase 1 Tasks): You own the Format Parsers (Other Formats) and Output generation. Please implement the following [MUST] tasks:

Implement FormatParser classes for Word documents (.docx), Excel spreadsheets (.xlsx), and generic HTML files.
Format Routing (core/router.py): Ensure file types correctly route to your format parsers or the existing pdf/image pipelines.
Output Generation (cli/export.py): Build export functions to convert the parsed Document schema into raw Markdown and JSON strings.
Register all your parsers using register_format_parser!
Please work on the main branch. Commit your changes and push directly to main. Be sure to update docs/HANDOFF_AGENT_4.md when you are done! Let's get started.

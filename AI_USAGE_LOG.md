# AI Usage Log

This project used AI coding assistants heavily during development, as
permitted by the brief. In the interest of transparency: **most of the
code in this repository (the Python backend, Gemini prompt design, JSON
schema, parsing logic, HTML template rendering, and test suite) was
written with AI assistance (Claude, by Anthropic).** The parts that were
not AI-generated are the initial project idea/direction and the visual
design of the frontend homepage and portfolio templates (layout choices,
styling decisions, and overall look), which the team designed itself.

Every AI-generated suggestion was still reviewed, run, and tested by the
team before being kept in the codebase. Nothing was merged without
understanding what it does. This log records the sessions.

---

### Entry 0: Initial project build (multiple sessions, multiple teammates)

- **AI tool used:** Claude (Anthropic)
- **Prompt / request given:** Development happened across many separate
  Claude conversations, spread across different teammates, over Weeks 1–2.
  Rather than list every individual prompt, the main categories of requests
  made to Claude were:
  - Setting up the Flask app structure and file upload routes
  - Writing the Gemini API integration and designing the extraction prompt
    (including the "don't invent information" rules)
  - Building the resume parsers for `.txt`, `.pdf`, and `.docx` files
  - Writing the JSON schema (Pydantic) for the structured resume data
  - Writing the frontend upload/template-selection JavaScript (`app.js`)
  - Writing the initial test suite for the parsing logic
- **What the tool generated:** First working versions of `app.py`,
  `ai/gemini.py`, `parsing/` (all four files), `static/js/app.js`, and
  `tests/test_parsing.py`.
- **What was changed/corrected before using it:** Each teammate reviewed
  their piece before merging, running it against real and sample resumes
  and fixing issues as they came up (e.g. prompt wording, parsing edge
  cases) rather than committing Claude's first-pass output unchanged.


### Entry 1: Server-side portfolio.html generation

- **AI tool used:** Claude (Anthropic)
- **Prompt / request given:** Asked whether the project met the brief's
  requirement, then asked to fix the top-priority gap: `portfolio.html` was
  never written to disk by Python. The web app filled templates in
  client-side via `localStorage` and JavaScript instead.
- **What the tool generated:** A `generator/html_generator.py` module using
  Jinja2 to render a `portfolio_template.html` + `portfolio_style.css` into a
  real `portfolio.html` file on disk, plus a wire-up in `main.py` so the CLI
  workflow (`resume.txt` → Gemini → JSON → `portfolio.html`) matches the
  brief exactly.
- **What was changed/corrected before using it:** Verified by actually
  running `python main.py` and confirming `portfolio.html` and
  `portfolio_style.css` appear on disk with real content (not just checking
  the code by eye).

### Entry 2: Clean configuration error instead of a crash

- **AI tool used:** Claude (Anthropic)
- **Prompt / request given:** Pointed out that a missing `google_api` key
  raised a raw `ValueError` traceback at import time instead of the clean
  `sys.exit("Configuration error: ...")` the brief's testing section expects.
- **What the tool generated:** Moved Gemini client creation out of
  module-level code and into a `_get_client()` function that raises a new
  `ConfigError` only when `get_resume_json()` is actually called; `main.py`
  now catches `ConfigError` specifically and exits cleanly with a readable
  message instead of a traceback.
- **What was changed/corrected before using it:** Removed the `.env` file
  locally and re-ran `python main.py` to confirm the output is now a single
  clean line (`Configuration error: google_api not found...`) with exit code
  1, not a traceback. Also checked that `app.py`'s existing `except
  Exception` still catches `ConfigError` correctly since it's unchanged.

### Entry 3: Text cleaning (blank lines / extra spaces)

- **AI tool used:** Claude (Anthropic)
- **Prompt / request given:** Noted the brief requires removing
  "unnecessary spaces and blank lines" before sending resume text to
  Gemini, but the code only called `.strip()` on the whole string.
- **What the tool generated:** A `_clean_text()` helper in
  `parsing/parser.py` that trims each line and collapses runs of multiple
  blank lines down to a single blank line, used by both the CLI
  (`read_resume`) and the web upload path (`extract_text_from_bytes`).
- **What was changed/corrected before using it:** Ran it against a sample
  string with irregular spacing/blank lines to confirm the output collapsed
  correctly, then re-ran the existing `pytest` suite (12 tests) to confirm
  nothing that depended on the old behavior broke.

### Entry 4: Documentation gaps (this file + README)

- **AI tool used:** Claude (Anthropic)
- **Prompt / request given:** Asked to add the mandatory AI usage log and a
  "Limitations & Hallucination Risks" section to the README, both called out
  as missing/required by the brief.
- **What the tool generated:** This file, and a new "Limitations &
  Hallucination Risks" section in `README.md` describing draft-quality
  output, the two synthesized fields (title/bio), PDF/DOCX parsing
  fragility, and the mitigations already in the prompt/code (low
  temperature, strict JSON schema, anti-fabrication rules, post-processing
  cleanup).
- **What was changed/corrected before using it:** Reviewed the limitations
  text against what the code actually does (e.g. confirmed `temperature=0.1`
  and `response_schema=ResumeData` in `ai/gemini.py` before citing them) so
  the README doesn't claim mitigations that aren't really there.

---

## What wasn't AI-generated

- The original idea/direction for the project (converting a resume into a
  portfolio site via Gemini).
- The visual design of the frontend homepage (`templates/index.html`,
  `static/css/sitepages.css`) and the two portfolio template layouts
  (`templates/template1.html`, `templates/template2.html`). The team made
  the styling and layout decisions for these.
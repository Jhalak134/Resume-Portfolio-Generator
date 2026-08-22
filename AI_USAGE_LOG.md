# AI Usage Log

This project used AI coding assistants during development, as permitted by
the brief. Every AI-generated suggestion was reviewed, tested, and understood
before being kept in the codebase. This log records the main sessions.

---

### Entry 1 — Server-side portfolio.html generation

- **AI tool used:** Claude (Anthropic)
- **Prompt / request given:** Asked whether the project met the brief's
  requirement, then asked to fix the top-priority gap: `portfolio.html` was
  never written to disk by Python — the web app filled templates in
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

### Entry 2 — Clean configuration error instead of a crash

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

### Entry 3 — Text cleaning (blank lines / extra spaces)

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

### Entry 4 — Documentation gaps (this file + README)

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

## Reminder for the group

Before submission, go back through this log and:
- Replace/extend entries with your own group's actual AI usage (ChatGPT,
  Gemini, Copilot, etc.), including anything from earlier weeks not covered
  here.
- Double-check every claim generated for the sample portfolio against the
  sample `resume.txt` — the brief requires this as a final verification step.
import base64
import io
import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("google_api")
if not API_KEY:
    raise ValueError(
        "google_api not found. Add it to your .env file, e.g.\n"
        "  google_api=YOUR_GEMINI_API_KEY"
    )

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.6-flash"


# ─────────────────────────────────────────────────────────────────────
# Main entry point — called by server.py
# ─────────────────────────────────────────────────────────────────────

def parse_resume_bytes(filename: str, data: bytes) -> dict:
    """Parse a resume file (PDF / DOCX / TXT) and return structured JSON.

    Strategy:
    - PDF:  Send raw bytes directly to Gemini (vision-aware, handles columns).
    - DOCX: Extract text with python-docx, then send text to Gemini.
    - TXT:  Send text directly to Gemini.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if not data or len(data.strip() if ext == "txt" else data) == 0:
        raise ValueError("File appears to be empty.")

    if ext == "pdf":
        return _gemini_pdf(data)

    elif ext == "docx":
        text = _extract_docx_text(data)
        return _gemini_text(text)

    elif ext == "txt":
        text = data.decode("utf-8", errors="ignore").strip()
        if len(text) < 50:
            raise ValueError("Resume text is too short to parse meaningfully.")
        return _gemini_text(text)

    else:
        raise ValueError(f"Unsupported file type: .{ext}. Please upload a PDF, DOCX, or TXT file.")


# ─────────────────────────────────────────────────────────────────────
# Gemini PDF (native — no text extraction, reads visually)
# ─────────────────────────────────────────────────────────────────────

def _gemini_pdf(pdf_bytes: bytes) -> dict:
    """Send PDF bytes directly to Gemini using inline file data.
    Gemini reads the PDF visually — handles columns, tables, any layout.
    """
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=pdf_b64,
                    )
                ),
                types.Part(text=_build_prompt("[See the attached PDF resume above]")),
            ],
        )
    ]

    return _call_gemini(contents)


# ─────────────────────────────────────────────────────────────────────
# Gemini Text (for DOCX / TXT after text extraction)
# ─────────────────────────────────────────────────────────────────────

def _gemini_text(resume_text: str) -> dict:
    """Send plain resume text to Gemini for structured extraction."""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=_build_prompt(resume_text))],
        )
    ]
    return _call_gemini(contents)


# ─────────────────────────────────────────────────────────────────────
# Shared Gemini caller with retry
# ─────────────────────────────────────────────────────────────────────

def _call_gemini(contents) -> dict:
    import time

    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            raw = _strip_fences(response.text)
            data = json.loads(raw)
            data = _sanitise(data)
            data = _post_validate(data)
            return data

        except json.JSONDecodeError as e:
            last_error = ValueError(
                f"Gemini returned invalid JSON: {e}\nRaw:\n{getattr(response, 'text', '')[:400]}"
            )
            break  # won't fix with retry

        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))

    raise last_error


# ─────────────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────────────

def _build_prompt(resume_text: str) -> str:
    return f"""\
You are an expert resume parser. Extract structured data from the resume and return ONLY a JSON object.

=== FIELD RULES ===

- name       : Full name of the person. Just the name, nothing else.
- title      : Job title / role (e.g. "Software Engineer"). Short phrase, not a sentence.
- bio        : Summary/Objective paragraph only. Clean 1–3 sentence description. Do NOT append section headings.
- email      : Email address only.
- phone      : Phone number only.
- location   : City and country/state only.
- linkedin   : Full URL (https://linkedin.com/in/...) or "".
- github     : Full URL (https://github.com/...) or "".
- twitter    : Full URL or "".
- website    : Personal site URL or "".
- skills     : List of individual skill/technology names. NOT sentences.
- education  : List of education entries:
    degree   → degree or course name ONLY (e.g. "B.Tech CSE", "Class XII"). NEVER a URL, email, or bio text.
    school   → institution name ONLY. NEVER a URL.
    year     → year or year range (e.g. "2021–2025").
- experience : List of work/internship entries:
    role     → job title ONLY (e.g. "Software Intern"). Max 60 characters.
    company  → employer name ONLY.
    duration → time period (e.g. "Jun 2024 – Aug 2024").
    bullets  → list of 2–4 short achievement phrases.
- projects   : List of projects:
    name     → SHORT project name only (1–6 words, e.g. "ClimateIQ Dashboard"). NOT a description.
    tech     → comma-separated stack (e.g. "React, Python, Firebase").
    github   → GitHub link if present, else "".
    demo     → live link if present, else "".
- achievements: Certifications, awards, hackathon wins:
    title    → short achievement title.
    sub      → issuer or year.

=== DO NOT ===
- Put URLs or emails in degree/school/role fields.
- Put bio sentences in role or degree fields.
- Put project descriptions in the project name field.
- Include section headings ("Education", "Skills", etc.) as content values.
- Hallucinate or invent information not present in the resume.

=== RESUME ===
\"\"\"
{resume_text}
\"\"\"

Return ONLY this JSON (no markdown, no explanation):

{{
  "name": "",
  "title": "",
  "bio": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "twitter": "",
  "website": "",
  "skills": [],
  "education": [{{"degree": "", "school": "", "year": ""}}],
  "experience": [{{"role": "", "company": "", "duration": "", "bullets": []}}],
  "projects": [{{"name": "", "tech": "", "github": "", "demo": ""}}],
  "achievements": [{{"title": "", "sub": ""}}]
}}"""


# ─────────────────────────────────────────────────────────────────────
# DOCX text extraction
# ─────────────────────────────────────────────────────────────────────

def _extract_docx_text(data: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(data))
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(lines)
    if len(text) < 50:
        raise ValueError("DOCX appears to have no readable text content.")
    return text


# ─────────────────────────────────────────────────────────────────────
# Post-processing & validation
# ─────────────────────────────────────────────────────────────────────

_JUNK = {
    "not found", "n/a", "none", "null", "na", "not provided",
    "not available", "not mentioned", "not specified", "unknown",
    "not applicable", "no information", "not stated", "-", "--",
}

_URL_RE    = re.compile(r"https?://|linkedin\.com|github\.com|twitter\.com", re.I)
_EMAIL_RE  = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
_HEADERS   = re.compile(
    r"^(education|experience|skills|projects|achievements|certifications|"
    r"summary|objective|profile|about|contact|references|work history|"
    r"internships?|publications?|awards?|honours?)$",
    re.I,
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _sanitise(obj):
    if isinstance(obj, dict):
        return {k: _sanitise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        cleaned = [_sanitise(i) for i in obj]
        return [i for i in cleaned if i not in ({}, "", [], None)]
    if isinstance(obj, str):
        s = obj.strip()
        return "" if s.lower() in _JUNK else s
    return obj


def _post_validate(data: dict) -> dict:
    # ── Education ──
    clean_edu = []
    for edu in data.get("education", []):
        deg    = edu.get("degree", "")
        school = edu.get("school", "")
        if _URL_RE.search(deg) or _EMAIL_RE.search(deg):
            continue
        if len(deg) > 80:
            edu["degree"] = deg[:80].rsplit(" ", 1)[0]
        if _HEADERS.match(deg.strip()) or _HEADERS.match(school.strip()):
            continue
        if _URL_RE.search(school) or _EMAIL_RE.search(school):
            edu["school"] = ""
        if edu.get("degree") or edu.get("school"):
            clean_edu.append(edu)
    data["education"] = clean_edu

    # ── Experience ──
    clean_exp = []
    for exp in data.get("experience", []):
        role = exp.get("role", "")
        if _URL_RE.search(role) or _EMAIL_RE.search(role):
            continue
        if len(role) > 60:
            exp["role"] = role[:60].rsplit(" ", 1)[0]
        if _HEADERS.match(role.strip()):
            continue
        if exp.get("role") or exp.get("company"):
            clean_exp.append(exp)
    data["experience"] = clean_exp

    # ── Projects ──
    clean_proj = []
    for proj in data.get("projects", []):
        name = proj.get("name", "").strip(" ,.-–:")
        if len(name) > 60:
            for sep in [",", " –", " -", ":", " |"]:
                if sep in name:
                    name = name.split(sep)[0].strip()
                    break
            name = name[:60]
        proj["name"] = name
        if proj.get("name"):
            clean_proj.append(proj)
    data["projects"] = clean_proj

    # ── Bio cleanup ──
    bio = data.get("bio", "")
    bio = re.sub(
        r"\s*(Education|Skills|Experience|Projects|Achievements|Contact|"
        r"References|Internship|Certifications)\s*$",
        "", bio, flags=re.I
    ).strip()
    if _URL_RE.search(bio):
        bio = re.sub(r"https?://\S+", "", bio).strip()
    data["bio"] = bio

    # ── Links ──
    for field in ("linkedin", "github", "twitter", "website"):
        val = data.get(field, "")
        if val and not val.startswith("http"):
            val = "https://" + val
        if val and not re.match(r"https?://\S+\.\S+", val):
            val = ""
        data[field] = val

    return data


# ─────────────────────────────────────────────────────────────────────
# Legacy helpers (kept for CLI / backward compat)
# ─────────────────────────────────────────────────────────────────────

def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """Legacy: extract raw text (used by /api/parse-resume endpoint)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "txt":
        text = data.decode("utf-8", errors="ignore").strip()
    elif ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                t = page.extract_text(extraction_mode="layout") or ""
            except Exception:
                t = page.extract_text() or ""
            pages.append(t)
        text = "\n".join(pages).strip()
    elif ext == "docx":
        text = _extract_docx_text(data)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")
    if not text or len(text) < 50:
        raise ValueError("Resume is empty or too short.")
    return text


def get_resume_json(resume_text: str) -> dict:
    """Legacy: parse from text string (used by /api/extract-portfolio)."""
    return _gemini_text(resume_text)


def read_resume(filepath: str) -> str:
    """Legacy: read a local text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError(f"File not found: {filepath}")

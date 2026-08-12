

import io
import json
import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("google_api")
if not API_KEY:
    raise ValueError(
        "google_api not found. Add it to your .env file, e.g.\n"
        "  google_api=YOUR_GEMINI_API_KEY"
    )

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash"


# ---------------------------------------------------------------------
# Text extraction (txt / pdf / docx)
# ---------------------------------------------------------------------

def read_resume(filepath: str) -> str:
    """Read + validate a local resume.txt (used by the CLI)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise ValueError(f"Error: '{filepath}' not found. Please check the file path.")

    return _validate(content)


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """Extract plain text from an uploaded file's raw bytes.

    Supports .txt, .pdf, and .docx — this is what backs the
    /api/parse-resume endpoint so PDF/DOCX uploads actually work
    instead of silently failing in the browser.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "txt":
        text = data.decode("utf-8", errors="ignore")

    elif ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    elif ext == "docx":
        import docx
        document = docx.Document(io.BytesIO(data))
        text = "\n".join(p.text for p in document.paragraphs)

    else:
        raise ValueError(f"Unsupported file type: .{ext}. Please upload a PDF, DOCX, or TXT file.")

    return _validate(text)


def _validate(content: str) -> str:
    cleaned = content.strip()

    if not cleaned:
        raise ValueError("Error: resume is empty. Please add your resume content.")

    MIN_LENGTH = 50
    if len(cleaned) < MIN_LENGTH:
        raise ValueError(
            f"Error: resume seems too short ({len(cleaned)} chars). "
            f"Please provide a complete resume with at least {MIN_LENGTH} characters."
        )

    return cleaned


# ---------------------------------------------------------------------
# Gemini extraction
# ---------------------------------------------------------------------

# NOTE: this schema is intentionally flat and matches the field names
# template1.html's populateFromData() actually reads (title/bio/email
# at top level, education[].school, experience[].bullets,
# projects[].name/tech, achievements[].title/sub). The original schema
# in this file used nested "contact" / "headline" / "summary" / etc,
# which template1.html never looked for, so the AI-parsed data was
# effectively discarded even when the backend worked.
PROMPT_TEMPLATE = """You are a resume parser. Convert the resume text below into a JSON object matching EXACTLY this schema. Do not invent, assume, or add any information that is not explicitly present in the resume text. If a field has no information, use an empty string "" or empty list [].

Return ONLY valid JSON. No markdown code fences, no explanations, no extra text before or after the JSON.

Schema:
{{
  "name": "",
  "title": "",
  "bio": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "skills": [],
  "education": [{{"degree": "", "school": "", "year": ""}}],
  "experience": [{{"role": "", "company": "", "duration": "", "bullets": []}}],
  "projects": [{{"name": "", "tech": "", "github": "", "demo": ""}}],
  "achievements": [{{"title": "", "sub": ""}}]
}}

Notes:
- "linkedin" and "github" should be full URLs if present (e.g. "https://linkedin.com/in/...").
- "bullets" should be short responsibility/achievement phrases, not full paragraphs.
- "tech" is a short comma-separated string of technologies used in that project.
- if these not presets put not found

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""


def _strip_code_fences(text: str) -> str:
    """Gemini sometimes wraps JSON in ```json ... ``` even when told not to."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def get_resume_json(resume_text: str) -> dict:
    """Call Gemini and return a parsed dict matching the schema above."""
    prompt = PROMPT_TEMPLATE.format(resume_text=resume_text)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    raw = _strip_code_fences(response.text)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini did not return valid JSON: {e}\nRaw response:\n{raw}")

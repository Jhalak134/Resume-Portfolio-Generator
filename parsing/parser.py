"""Format-agnostic entry points used by the Flask routes and the CLI.

Dispatches to txt_parser / pdf_parser / docx_parser based on file
extension, and validates the resulting text is non-empty and long
enough to be worth sending to Gemini.
"""

from . import docx_parser, pdf_parser, txt_parser

MIN_LENGTH = 50


def _validate(content: str) -> str:
    cleaned = content.strip()

    if not cleaned:
        raise ValueError("Error: resume is empty. Please add your resume content.")

    if len(cleaned) < MIN_LENGTH:
        raise ValueError(
            f"Error: resume seems too short ({len(cleaned)} chars). "
            f"Please provide a complete resume with at least {MIN_LENGTH} characters."
        )

    return cleaned


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
        text = txt_parser.extract_text(data)
    elif ext == "pdf":
        text = pdf_parser.extract_text(data)
    elif ext == "docx":
        text = docx_parser.extract_text(data)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Please upload a PDF, DOCX, or TXT file.")

    return _validate(text)


def extract_photo_from_bytes(filename: str, data: bytes) -> str:
    """Best-effort extraction of an embedded photo from a PDF/DOCX resume.
    Returns a base64 data URI or "" if none found / .txt file."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "docx":
        return docx_parser.extract_photo(data)
    if ext == "pdf":
        return pdf_parser.extract_photo(data)
    return ""

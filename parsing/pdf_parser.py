"""PDF resume extraction: plain text and a best-effort embedded photo."""

import base64
import io


def extract_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_photo(data: bytes) -> str:
    """Return a base64 data URI for the first embedded image found, or ""."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            for image in page.images:
                img_ext = (image.name.rsplit(".", 1)[-1] if "." in image.name else "png").lower()
                mime = "image/jpeg" if img_ext in ("jpg", "jpeg") else f"image/{img_ext}"
                b64 = base64.b64encode(image.data).decode("ascii")
                return f"data:{mime};base64,{b64}"
    except Exception:
        pass
    return ""

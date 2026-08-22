"""Plain-text resume extraction (.txt files)."""


def extract_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")

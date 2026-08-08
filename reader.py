def read_resume(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise ValueError(f"Error: '{filepath}' not found. Please check the file path.")

    cleaned = content.strip()

    if not cleaned:
        raise ValueError("Error: resume.txt is empty. Please add your resume content.")

    MIN_LENGTH = 50  # tweak this threshold as needed
    if len(cleaned) < MIN_LENGTH:
        raise ValueError(
            f"Error: resume.txt seems too short ({len(cleaned)} chars). "
            f"Please provide a complete resume with at least {MIN_LENGTH} characters."
        )

    return cleaned
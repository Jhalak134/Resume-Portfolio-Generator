import os
from dotenv import load_dotenv
from google import genai

# ---- Step 1: Load API key ----
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=API_KEY)

# ---- Step 2: Resume reading/cleaning ----
def read_resume(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise ValueError(f"Error: '{filepath}' not found. Please check the file path.")

    cleaned = content.strip()

    if not cleaned:
        raise ValueError("Error: resume.txt is empty. Please add your resume content.")

    MIN_LENGTH = 50
    if len(cleaned) < MIN_LENGTH:
        raise ValueError(
            f"Error: resume.txt seems too short ({len(cleaned)} chars). "
            f"Please provide a complete resume with at least {MIN_LENGTH} characters."
        )

    return cleaned

# ---- Step 3: The prompt ----
PROMPT_TEMPLATE = """You are a resume parser. Convert the resume text below into a JSON object matching EXACTLY this schema. Do not invent, assume, or add any information that is not explicitly present in the resume text. If a field has no information, use an empty string "" or empty list [].

Return ONLY valid JSON. No markdown code fences, no explanations, no extra text before or after the JSON.

Schema:
{{
  "name": "",
  "headline": "",
  "summary": "",
  "skills": [],
  "education": [{{"degree": "", "institution": "", "year": ""}}],
  "experience": [{{"role": "", "company": "", "duration": "", "description": ""}}],
  "projects": [{{"title": "", "description": "", "technologies": []}}],
  "achievements": [],
  "contact": {{"email": "", "phone": "", "linkedin": "", "github": "", "other_links": []}}
}}

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""

# ---- Step 4: Function to call Gemini (NEW SDK syntax) ----
def get_resume_json(resume_text: str) -> str:
    prompt = PROMPT_TEMPLATE.format(resume_text=resume_text)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    return response.text

# ---- Step 5: Run it ----
if __name__ == "__main__":
    resume_text = read_resume("resume.txt")
    raw_output = get_resume_json(resume_text)
    print(raw_output)
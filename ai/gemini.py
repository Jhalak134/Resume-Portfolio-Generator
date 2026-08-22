"""Gemini client: turns validated resume text into structured portfolio JSON."""

import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

API_KEY = os.getenv("google_api")
if not API_KEY:
    raise ValueError(
        "google_api not found. Add it to your .env file, e.g.\n"
        "  google_api=YOUR_GEMINI_API_KEY"
    )

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash"


class EducationItem(BaseModel):
    degree: str = ""
    school: str = ""
    year: str = ""


class ExperienceItem(BaseModel):
    role: str = ""
    company: str = ""
    duration: str = ""
    bullets: list[str] = []


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    tech: str = ""
    github: str = ""
    demo: str = ""


class AchievementItem(BaseModel):
    title: str = ""
    sub: str = ""


class ResumeData(BaseModel):
    name: str = ""
    title: str = ""
    bio: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    skills: list[str] = []
    education: list[EducationItem] = []
    experience: list[ExperienceItem] = []
    projects: list[ProjectItem] = []
    achievements: list[AchievementItem] = []


PROMPT_TEMPLATE = """You are a resume parser and professional profile generator.

Convert the resume text below into a JSON object matching the given schema.

GENERAL RULE:
Extract factual information from the resume accurately. Do not fabricate or assume information that is not supported by the resume.

There are TWO special fields that may be generated when missing:

1. TITLE GENERATION
If the resume explicitly contains a professional title, job title, role, headline, or designation, extract it accurately.

If no professional title is explicitly present, generate a concise professional title based ONLY on information supported by the resume, including education, skills, experience, and projects.

The generated title should:
- Be concise, preferably 3-7 words.
- Represent the candidate's actual profile.
- Reflect their strongest relevant skills or field.
- Avoid exaggerating seniority or experience.
- Never introduce a technology, role, qualification, or specialization that is not supported by the resume.

For example, if the resume contains:
B.Tech in Computer Science + Python + Machine Learning + ML projects

A suitable generated title could be:
"Computer Science & ML Enthusiast"

Do NOT generate:
"Senior Machine Learning Engineer"
unless the resume clearly supports that level of professional experience.

2. BIO GENERATION
If the resume explicitly contains a summary, objective, profile, about section, or professional description, extract it accurately.

If no such summary exists, generate a short professional bio based ONLY on factual information supported by the resume.

The generated bio should:
- Be 1-2 concise sentences.
- Mention the candidate's field, relevant skills, experience, education, or projects when appropriate.
- Be professional and suitable for a portfolio website.
- Never invent years of experience, companies, achievements, certifications, responsibilities, or technologies.
- Never exaggerate the candidate's expertise or seniority.

IMPORTANT:
Generated title and bio are the ONLY fields where synthesis is allowed.

For all other fields, extract information only when explicitly supported by the resume. If information is genuinely missing, return "" or [].

Never fabricate:
- email
- phone
- location
- LinkedIn
- GitHub
- skills
- education
- experience
- projects
- achievements
- dates
- companies
- certifications
- qualifications
- technologies

CRITICAL RULES — read carefully, these have caused mistakes before:
1. Each numbered or bulleted item (e.g. "1.", "2)", "-") in a "Projects" or "Education" section is exactly ONE entry. Never split a single numbered item into multiple entries, and never let text from one numbered item leak into the previous or next entry.
2. Never split an entry's text at a comma or period unless the resume itself starts a genuinely new item there (e.g. a new number, a new bullet, or a blank line). "Developed a tool to manage records, attendance and grades." is ONE description, not three.
3. Put the one-line project summary in "description", not in "tech" or "name". "tech" is ONLY a short comma-separated list of technology/tool names (e.g. "Python, Flask, SQL") — if no technologies are explicitly named for a project, leave "tech" as "".
4. "name" for a project or "degree"/"school" for education must be a real, complete label copied from the resume — never a lone number, a lone letter, or a sentence fragment like "and grades." or "ment".
5. If a paragraph in the resume runs across multiple lines but is clearly about ONE item (no new number/bullet/heading), treat it as ONE entry and merge the lines together.
6. "linkedin" and "github" should be full URLs if present (e.g. "https://linkedin.com/in/...").
7. "bullets" (experience) should be short responsibility/achievement phrases, not full paragraphs.
8. If a field genuinely isn't present anywhere in the resume, use "" or [] — do not guess or fabricate.
9. If title is missing from the resume, generate it using only evidence from the resume. If an explicit title exists, prefer the explicit title.

10. If bio/summary is missing from the resume, generate a concise 1-2 sentence portfolio bio using only evidence from the resume. If an explicit summary exists, preserve its meaning while cleaning minor formatting issues if necessary.

11. When generating title or bio, consider multiple relevant pieces of evidence when available, such as education, skills, projects, and experience.

12. Never infer a level of seniority that is not supported by the resume. Prefer terms such as "Student", "Aspiring", "Enthusiast", or "Developer" when appropriate rather than claiming senior-level expertise.

13. Generated title and bio must remain consistent with the actual resume and must not introduce unsupported facts.

14. Location must never be generated. If location is not present in the resume, return "".

Worked example — given this resume fragment:
\"\"\"
Education:
B.Tech in Computer Science, ABC University, 2022-2026

Projects:
1. Student Management System - Built a tool to manage student records, attendance and grades. Tech: Python, Flask.
2. Personal Portfolio Website - A personal site to showcase work.
\"\"\"
The correct output for those two sections is:
"education": [{{"degree": "B.Tech in Computer Science", "school": "ABC University", "year": "2022-2026"}}]
"projects": [
  {{"name": "Student Management System", "description": "Built a tool to manage student records, attendance and grades.", "tech": "Python, Flask", "github": "", "demo": ""}},
  {{"name": "Personal Portfolio Website", "description": "A personal site to showcase work.", "tech": "", "github": "", "demo": ""}}
]
Notice each numbered item stayed intact as ONE entry, and the description was NOT split at its internal commas.

Return ONLY valid JSON matching the schema. No markdown code fences, no explanations, no extra text before or after the JSON.

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


_LEADING_ENUM_RE = re.compile(r"^\s*(?:\d+[.)]|[-•*])\s+")
_LEADING_CONJUNCTION_RE = re.compile(r"^(and|or|but|with|the|a|an)\s", re.IGNORECASE)


def _clean_label(value: str) -> str:
    """Strip stray leading numbering ("1. ", "2) ", "- ") that sometimes
    survives into a name/degree/title field, and collapse whitespace."""
    if not isinstance(value, str):
        return value
    value = _LEADING_ENUM_RE.sub("", value.strip())
    return re.sub(r"\s+", " ", value).strip()


def _is_degenerate(value: str) -> bool:
    """Flag obviously-broken fragments: empty, a lone character/number, or
    a sentence-tail that leaked from the previous item (e.g. "and grades.",
    starts with a lowercase conjunction/article)."""
    if not value:
        return False
    stripped = value.strip()
    if len(stripped) <= 2:
        return True
    if _LEADING_CONJUNCTION_RE.match(stripped):
        return True
    return False


def _clean_tech(value: str) -> str:
    """"tech" should be a short comma-separated list of tool/technology
    names. If it instead looks like a sentence fragment (long segments,
    stray periods) that leaked in from a description, discard it rather
    than render garbled badges on the portfolio."""
    if not isinstance(value, str) or not value.strip():
        return ""
    segments = [s.strip() for s in re.split(r"[,/·]", value) if s.strip()]
    for seg in segments:
        if "." in seg or len(seg.split()) > 4:
            return ""
    return ", ".join(segments)


def _clean_resume_data(data: dict) -> dict:
    """Post-process the parsed JSON: trim stray numbering off labels and
    drop entries that are clearly fragments rather than real items, so a
    single bad split doesn't render as a garbled card on the portfolio."""
    for proj in data.get("projects", []) or []:
        proj["name"] = _clean_label(proj.get("name", ""))
        proj["tech"] = _clean_tech(proj.get("tech", ""))
    data["projects"] = [
        p for p in (data.get("projects") or [])
        if not _is_degenerate(p.get("name", ""))
    ]

    for edu in data.get("education", []) or []:
        edu["degree"] = _clean_label(edu.get("degree", ""))
        edu["school"] = _clean_label(edu.get("school", ""))
    data["education"] = [
        e for e in (data.get("education") or [])
        if not _is_degenerate(e.get("degree", "")) or not _is_degenerate(e.get("school", ""))
    ]

    return data


def get_resume_json(resume_text: str) -> dict:
    """Call Gemini and return a parsed dict matching the schema above."""
    prompt = PROMPT_TEMPLATE.format(resume_text=resume_text)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResumeData,
            temperature=0.1,
        ),
    )

    raw = _strip_code_fences(response.text)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini did not return valid JSON: {e}\nRaw response:\n{raw}")

    # TEMPORARY DEBUG: inspect AI-generated profile fields
    print("\n========== AI RESUME OUTPUT ==========")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("======================================\n")

    return _clean_resume_data(data)

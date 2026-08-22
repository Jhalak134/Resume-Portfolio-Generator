"""
main.py
-------
CLI entry point: reads resume.txt from the current directory,
sends it to Gemini, and prints the structured JSON.

For the actual web app (templates/index.html + static/js/app.js +
templates/template1.html), run app.py instead — that's what serves
the /api endpoints the frontend calls.
"""

import json

from ai import get_resume_json
from parsing import read_resume

if __name__ == "__main__":
    resume_text = read_resume("resume.txt")
    data = get_resume_json(resume_text)
    print(json.dumps(data, indent=2))

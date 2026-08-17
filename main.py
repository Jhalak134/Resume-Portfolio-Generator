import json
from resume_ai import read_resume, get_resume_json

if __name__ == "__main__":
    resume_text = read_resume("resume.txt")
    data = get_resume_json(resume_text)
    print(json.dumps(data, indent=2))
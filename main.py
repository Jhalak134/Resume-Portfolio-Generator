import json
import os
import sys

from ai import ConfigError, get_resume_json
from generator import generate_portfolio_html
from parsing import read_resume

if __name__ == "__main__":
    default_path = "resume.txt" if os.path.exists("resume.txt") else "sample_resume.txt"
    filepath = sys.argv[1] if len(sys.argv) > 1 else default_path

    try:
        resume_text = read_resume(filepath)
    except ValueError as e:
        sys.exit(f"Input error: {e}")

    try:
        data = get_resume_json(resume_text)
    except ConfigError as e:
        sys.exit(f"Configuration error: {e}")
    except ValueError as e:
        sys.exit(f"Gemini returned unusable data: {e}")
    except Exception as e:
        sys.exit(f"Gemini request failed: {e}")

    print(json.dumps(data, indent=2))

    output_path = generate_portfolio_html(data, output_dir=".")
    print(f"\nPortfolio written to {output_path}")
    print("Open it in a browser to view it.")
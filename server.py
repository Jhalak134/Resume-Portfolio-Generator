"""
server.py
---------
Flask backend for the Resume Portfolio Generator.

Serves the existing frontend (index.html / app.js / style.css /
template1.html) as static files, and implements two API endpoints:

  POST /api/generate-portfolio  -> { ...structured portfolio JSON... }
  POST /api/parse-resume        -> { text: "<extracted resume text>" }  (legacy)
  POST /api/extract-portfolio   -> { ...structured portfolio JSON... }  (legacy)

Run with:
    python server.py
Then open http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
import traceback

from resume_ai import extract_text_from_bytes, get_resume_json, parse_resume_bytes

app = Flask(__name__, static_folder=".", static_url_path="")


# ---------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# Flask's static_url_path="" already serves style.css, app.js,
# template1.html, etc. straight from this folder.


# ---------------------------------------------------------------------
# API: one-shot file → portfolio JSON  (primary endpoint)
# ---------------------------------------------------------------------

@app.route("/api/generate-portfolio", methods=["POST"])
def generate_portfolio():
    """Accept a raw resume file and return structured portfolio JSON.

    PDFs are sent directly to Gemini as inline file data (vision mode),
    which reads the layout visually — no text extraction step needed.
    DOCX and TXT are extracted to text first, then parsed by Gemini.
    """
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded under field name 'resume'."}), 400

    file = request.files["resume"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    file_bytes = file.read()
    if not file_bytes:
        return jsonify({"error": "The uploaded file is empty."}), 400

    try:
        data = parse_resume_bytes(file.filename, file_bytes)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Parsing failed: {e}"}), 502

    return jsonify(data)



# ---------------------------------------------------------------------
# API (legacy): extract raw text from an uploaded PDF/DOCX/TXT
# ---------------------------------------------------------------------

@app.route("/api/parse-resume", methods=["POST"])
def parse_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded under field name 'resume'."}), 400

    file = request.files["resume"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    try:
        text = extract_text_from_bytes(file.filename, file.read())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()  # full stack trace in the terminal for debugging
        return jsonify({"error": f"Failed to read file: {e}"}), 500

    return jsonify({"text": text})


# ---------------------------------------------------------------------
# API (legacy): turn resume text into structured portfolio JSON via Gemini
# ---------------------------------------------------------------------

@app.route("/api/extract-portfolio", methods=["POST"])
def extract_portfolio():
    body = request.get_json(silent=True) or {}
    resume_text = (body.get("text") or "").strip()

    if not resume_text:
        return jsonify({"error": "No resume text provided."}), 400
    if len(resume_text) < 50:
        return jsonify({"error": "Resume text is too short to parse."}), 400

    try:
        data = get_resume_json(resume_text)
    except ValueError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"Gemini request failed: {e}"}), 502

    return jsonify(data)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
"""
server.py
---------
Flask backend for the Resume Portfolio Generator.

Serves the existing frontend (index.html / app.js / style.css /
template1.html) as static files, and implements the two endpoints
app.js already calls but that previously did not exist:

  POST /api/parse-resume       -> { text: "<extracted resume text>" }
  POST /api/extract-portfolio  -> { ...structured portfolio JSON... }

Run with:
    python server.py
Then open http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
import traceback

from resume_ai import extract_text_from_bytes, get_resume_json

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
# API: extract raw text from an uploaded PDF/DOCX/TXT
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
# API: turn resume text into structured portfolio JSON via Gemini
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
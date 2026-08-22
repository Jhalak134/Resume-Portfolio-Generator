from flask import Flask, jsonify, render_template, request

from ai import get_resume_json
from config import Config
from parsing import extract_photo_from_bytes, extract_text_from_bytes

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


@app.route("/template1.html")
def template1():
    return render_template("template1.html")


@app.route("/template2.html")
def template2():
    return render_template("template2.html")


@app.route("/sitepages/<page>.html")
def sitepage(page):
    return render_template(f"sitepages/{page}.html")


@app.route("/api/parse-resume", methods=["POST"])
def parse_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded under field name 'resume'."}), 400

    file = request.files["resume"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    raw_bytes = file.read()

    try:
        text = extract_text_from_bytes(file.filename, raw_bytes)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {e}"}), 500

    photo = extract_photo_from_bytes(file.filename, raw_bytes)
    return jsonify({"text": text, "photo": photo})


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
        print("\n========== RESUME PARSING ERROR ==========")
        print(e)
        print("==========================================\n")
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        print("\n========== GEMINI REQUEST ERROR ==========")
        print(repr(e))
        print("==========================================\n")
        return jsonify({"error": f"Gemini request failed: {e}"}), 502

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

#!/usr/bin/env python3
"""
Simple Flask backend for the autofill demo.

- Serves the enhanced `sample_form.html` (GET /)
- Handles the form POST to /submit and writes a JSON record to `submissions/`.
- Provides a quick read‑only endpoint /submissions that returns all saved data.
"""

import json
import pathlib
import datetime
from flask import Flask, request, jsonify, send_from_directory, abort

app = Flask(__name__, static_folder=str(pathlib.Path(__file__).parent))

# ---------------------------------------------------------------------------
# Helper paths
BASE_DIR = pathlib.Path(__file__).parent
SUBMISSIONS = BASE_DIR / "submissions"
FORM_FILE = BASE_DIR / "sample_form.html"

# Ensure the folder exists
SUBMISSIONS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    """Serve the static HTML form."""
    if not FORM_FILE.is_file():
        abort(404, description="sample_form.html not found")
    return send_from_directory(BASE_DIR, FORM_FILE.name)

@app.route("/submit", methods=["POST"])
def submit():
    """Receive form data, store it as a JSON file, and reply with a thank‑you page."""
    # Convert ImmutableMultiDict to plain dict, ignore empty file uploads.
    data = {k: v for k, v in request.form.items()}
    for f in request.files.values():
        if f and f.filename:
            data[f.name] = f.filename
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = SUBMISSIONS / f"submission_{ts}.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return """
    <!DOCTYPE html>
    <html lang=\"en\"><head><meta charset=\"utf-8\"><title>Thanks</title>
    <style>body{font-family:Helvetica,Arial,sans-serif;text-align:center;padding:2rem;background:#f0f4f8}h1{color:#2c3e50}</style></head>
    <body><h1>Thank you!</h1><p>Your application has been recorded.</p><p><a href=\"/\">Back to form</a></p></body></html>
    """

@app.route("/submissions", methods=["GET"])
def list_submissions():
    """Return a JSON array with all saved submissions (read‑only)."""
    records = []
    for p in sorted(SUBMISSIONS.glob("submission_*.json")):
        try:
            records.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return jsonify(records)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)

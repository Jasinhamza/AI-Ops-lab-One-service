import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
WHISPER_URL = os.getenv("WHISPER_URL", "http://localhost:9000")

API_KEY = os.getenv("API_KEY")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/transcribe")

def transcribe():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify(error="unauthorized"), 401

    if "file" not in request.files:
        return jsonify(error="send a file in the 'file' field"), 400

    clip = request.files["file"]
    try:
        r = requests.post(
            f"{WHISPER_URL}/asr",
            params={"output": "json"},
            files={"audio_file": (clip.filename, clip.stream, clip.mimetype)},
            timeout=120,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        app.logger.error("whisper call failed: %s", type(e).__name__)
        return jsonify(error="transcription service unavailable"), 502

    return jsonify(text=r.json().get("text", ""))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
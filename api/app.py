import os
import time
import requests
from flask import Flask, request, jsonify, g, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUESTS = Counter(
    "api_requests_total",
    "HTTP requests handled",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "api_request_duration_seconds",
    "Time to handle a request",
    ["endpoint"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120],
)

app = Flask(__name__)
WHISPER_URL = os.getenv("WHISPER_URL", "http://localhost:9000")
API_KEY = os.getenv("API_KEY")


@app.before_request
def start_timer():
    g.start = time.time()


@app.after_request
def record_metrics(response):
    if request.path not in ("/metrics", "/healthz"):
        duration = time.time() - g.start
        REQUESTS.labels(request.method, request.path, response.status_code).inc()
        LATENCY.labels(request.path).observe(duration)
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


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
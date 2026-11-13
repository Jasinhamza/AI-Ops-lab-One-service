import os
import time
import requests
from prometheus_client import Gauge, Counter, start_http_server

API_URL = os.getenv("API_URL", "http://api/transcribe")
API_KEY = os.getenv("API_KEY", "")
INTERVAL = int(os.getenv("INTERVAL_SECONDS", "60"))

SUCCESS = Gauge("synthetic_check_success", "1 if the last check passed, 0 if it failed")
LAST_OK = Gauge("synthetic_check_last_success_timestamp_seconds", "Unix time of the last passing check")
DURATION = Gauge("synthetic_check_duration_seconds", "How long the last check took")
RUNS = Counter("synthetic_check_runs_total", "Checks run", ["result"])

def check():
    start = time.time()
    try:
        with open("short.wav", "rb") as f:
            r = requests.post(API_URL, headers={"X-API-Key": API_KEY},
                              files={"file": ("short.wav", f, "audio/wav")}, timeout=60)
        ok = r.status_code == 200 and r.json().get("text", "").strip() != ""
        reason = f"status {r.status_code}"
    except Exception as e:
        ok = False
        reason = type(e).__name__
    took = time.time() - start
    DURATION.set(took)
    SUCCESS.set(1 if ok else 0)
    if ok:
        LAST_OK.set_to_current_time()
    RUNS.labels("ok" if ok else "fail").inc()
    print(f"check {'ok' if ok else 'FAILED'} ({reason}) in {took:.1f}s", flush=True)

if __name__ == "__main__":
    start_http_server(8000)
    while True:
        check()
        time.sleep(INTERVAL)
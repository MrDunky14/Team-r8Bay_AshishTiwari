"""
Project Aegis-Voice: Master System Launcher
Boots the unified FastAPI/WebSocket Ingestion Gateway & Operator Dispatch Console.
Serves the 60fps WebGL/HTML5 Command Dashboard at http://127.0.0.1:8080.
"""

import sys
import os
import webbrowser
import threading
import time
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
INGESTION_DIR = os.path.join(CORE_DIR, "ingestion-gateway")

# Add directories to sys.path
sys.path.insert(0, os.path.join(CORE_DIR, "semantic-asr-worker"))
sys.path.insert(0, os.path.join(CORE_DIR, "acoustic-ser-worker"))
sys.path.insert(0, os.path.join(CORE_DIR, "neuro-symbolic-triage"))
sys.path.insert(0, INGESTION_DIR)

from ws_ingest_server import app

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8080"
    print(f"\n[AEGIS-VOICE] Opening Operator Dispatch Console at: {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 70)
    print("PROJECT AEGIS-VOICE: 1930 EMERGENCY TRIAGE CORE")
    print("=" * 70)
    print("Starting Ingestion Gateway, Late-Fusion Engine & WebSockets on port 8080...")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")

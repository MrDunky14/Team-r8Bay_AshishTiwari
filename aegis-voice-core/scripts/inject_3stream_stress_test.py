"""
Project Aegis-Voice: 1-Click 3-Stream Stress Test Injector
Simulates the 3-stream benchmark for Slide 3 & Slide 4 live demonstrations:
- Stream #104: Loud Non-Urgent Caller -> Capped at 0.41 (AGITATED - ROUTINE)
- Stream #105: Synthetic Voice Deepfake Bot -> AASIST-L Spoof 94% -> Urgency 0.15 (BLOCKED)
- Stream #106: Stoic Shock Victim (₹12L Digital Arrest) -> Auto-promoted to Top with Urgency 0.86
"""

import sys
import json
import urllib.request
import urllib.error

ENDPOINT = "http://127.0.0.1:8080/api/stress-test"

def main():
    print(f"Connecting to Aegis-Voice Ingestion Gateway at {ENDPOINT}...")
    try:
        req = urllib.request.Request(ENDPOINT, data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("\n[SUCCESS] 3-Stream Stress Test Successfully Injected into Queue!")
            print(f"Status: {result.get('status')}")
            print("\nQueue Status after Dynamic Re-Ranking:")
            for item in result.get("queue", []):
                print(f"  • Rank #{item['stream_id']} | U(t): {item['urgency_score']} | {item['badge']} | {item['caller_name']}")
    except urllib.error.URLError as e:
        print(f"[NOTE] Local server at {ENDPOINT} is not currently running.")
        print("To start the server, execute: python aegis-voice-core/scripts/run_system.py")

if __name__ == "__main__":
    main()

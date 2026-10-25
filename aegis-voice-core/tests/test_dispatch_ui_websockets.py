"""
Tests for Microservice 6: Dispatch UI & WebSockets
- REST API endpoints: GET /api/health, GET /, POST /api/stress-test, POST /api/authorize-lien, POST /api/officer-override.
- WebSocket /ws/dispatch telemetry stream: initial queue broadcast, stream selection, dynamic queue re-ranking.
- One-click lien push authorization flow (S4 -> S5 state transition, lien_pushed flag).
"""

import os
import sys
import json
import time
import pytest
from starlette.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
INGESTION_DIR = os.path.join(CORE_DIR, "ingestion-gateway")
if INGESTION_DIR not in sys.path:
    sys.path.insert(0, INGESTION_DIR)

import ws_ingest_server
from ws_ingest_server import app


@pytest.fixture(autouse=True)
def reset_queue():
    """Ensure clean queue state before each test."""
    ws_ingest_server.initialize_default_queue()


def test_rest_health_check_and_sla_metrics():
    """Verify GET /api/health returns valid system status, zero-disk compliance, and latency SLAs."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "aegis-voice-core"
    assert data["status"] == "HEALTHY"
    assert data["dpdp_zero_disk_compliance"] == "VERIFIED_TMPFS_VOLATILE_ONLY"
    assert data["glass_to_glass_p50_ms"] < 800.0
    assert data["glass_to_glass_p99_ms"] < 800.0
    assert data["sla_target_ms"] == 800.0
    assert "shadow_mode_readiness" in data
    assert data["shadow_mode_readiness"]["golden_hour_gate_passed"] is True


def test_rest_root_endpoint():
    """Verify GET / root endpoint responds with status 200."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_rest_stress_test_trigger():
    """Verify POST /api/stress-test resets and sorts queue descending by urgency score."""
    client = TestClient(app)
    response = client.post("/api/stress-test")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "STRESS_TEST_EXECUTED"
    queue = body["queue"]
    assert len(queue) == 3

    # Top stream must be #106 (Stoic Shock Victim, Urgency 0.86)
    assert queue[0]["stream_id"] == "106"
    assert queue[0]["urgency_score"] == 0.86

    # Second stream must be #104 (Loud Yelling, Urgency 0.41)
    assert queue[1]["stream_id"] == "104"
    assert queue[1]["urgency_score"] == 0.41

    # Third stream must be #105 (Synthetic Spoof, Urgency 0.15)
    assert queue[2]["stream_id"] == "105"
    assert queue[2]["urgency_score"] == 0.15


def test_rest_authorize_lien_and_s4_to_s5_transition():
    """Verify one-click lien authorization flow transitions call state from S4 to S5."""
    client = TestClient(app)

    # 1. Invalid stream ID returns 404
    resp_invalid = client.post("/api/authorize-lien", json={"stream_id": "non-existent-999"})
    assert resp_invalid.status_code == 404

    # 2. Check initial pre-staged state of Stream #106 (S4)
    target_stream = next((c for c in ws_ingest_server.active_call_queue if c["stream_id"] == "106"), None)
    assert target_stream is not None
    assert target_stream["state"] == "S4_LIEN_PAYLOAD_STAGED"
    assert not target_stream.get("lien_pushed", False)

    # 3. Post authorization for Stream #106
    t0 = time.time()
    resp_valid = client.post("/api/authorize-lien", json={"stream_id": "106"})
    assert resp_valid.status_code == 200
    assert resp_valid.json()["status"] == "SUCCESS"

    # 4. Invariant assertion: S4 -> S5 transition and lien_pushed flag set
    assert target_stream["state"] == "S5_LIEN_DISPATCHED_TO_NPCI"
    assert target_stream["lien_pushed"] is True
    assert target_stream["lien_timestamp"] >= t0


def test_rest_officer_override_actions():
    """Verify manual dispatcher overrides re-rank the live emergency queue."""
    client = TestClient(app)

    # 1. Non-existent stream returns 404
    resp_404 = client.post("/api/officer-override", json={"stream_id": "999", "action": "DOWNGRADE_ROUTINE"})
    assert resp_404.status_code == 404

    # 2. DOWNGRADE_ROUTINE on Stream #106
    resp_routine = client.post("/api/officer-override", json={"stream_id": "106", "action": "DOWNGRADE_ROUTINE"})
    assert resp_routine.status_code == 200
    queue_routine = resp_routine.json()["queue"]
    stream_106 = next(c for c in queue_routine if c["stream_id"] == "106")
    assert stream_106["urgency_score"] == 0.30
    assert "ROUTINE" in stream_106["badge"]

    # 3. CONFIRM_GOLDEN_HOUR on Stream #104
    resp_golden = client.post("/api/officer-override", json={"stream_id": "104", "action": "CONFIRM_GOLDEN_HOUR"})
    assert resp_golden.status_code == 200
    queue_golden = resp_golden.json()["queue"]
    # Stream #104 escalated to 0.95 and auto-promoted to top of queue
    assert queue_golden[0]["stream_id"] == "104"
    assert queue_golden[0]["urgency_score"] == 0.95
    assert "GOLDEN HOUR" in queue_golden[0]["badge"]

    # 4. DOWNGRADE_ACOUSTIC_SPIKE
    resp_spike = client.post("/api/officer-override", json={"stream_id": "104", "action": "DOWNGRADE_ACOUSTIC_SPIKE"})
    assert resp_spike.status_code == 200
    queue_spike = resp_spike.json()["queue"]
    stream_104 = next(c for c in queue_spike if c["stream_id"] == "104")
    assert stream_104["urgency_score"] == 0.40
    assert "FALSE ACOUSTIC SPIKE" in stream_104["badge"]


def test_ws_dispatch_initial_state_and_selection():
    """Verify WebSocket /ws/dispatch telemetry broadcast, initial state payload, and stream selection."""
    client = TestClient(app)

    with client.websocket_connect("/ws/dispatch") as ws:
        # Receive INITIAL_QUEUE_STATE
        init_raw = ws.receive_text()
        init_msg = json.loads(init_raw)
        assert init_msg["type"] == "INITIAL_QUEUE_STATE"
        data = init_msg["data"]
        assert "queue" in data
        assert len(data["queue"]) >= 3
        assert "shadow_stats" in data
        assert data["shadow_stats"]["golden_hour_gate_passed"] is True
        assert data["selected_stream"]["stream_id"] == "106"

        # Action: SELECT_STREAM #104
        ws.send_text(json.dumps({"action": "SELECT_STREAM", "stream_id": "104"}))
        select_raw = ws.receive_text()
        select_msg = json.loads(select_raw)
        assert select_msg["type"] == "STREAM_SELECTED"
        assert select_msg["data"]["stream_id"] == "104"

        # Action: TRIGGER_3STREAM_STRESS_TEST
        ws.send_text(json.dumps({"action": "TRIGGER_3STREAM_STRESS_TEST"}))
        stress_raw = ws.receive_text()
        stress_msg = json.loads(stress_raw)
        assert stress_msg["type"] == "QUEUE_UPDATED"
        assert stress_msg["data"]["queue"][0]["stream_id"] == "106"


def test_ws_dispatch_multiple_clients_and_clean_teardown():
    """Verify multiple UI dispatcher clients connect, receive broadcasts, and cleanly disconnect."""
    client = TestClient(app)

    with client.websocket_connect("/ws/dispatch") as ws1:
        assert len(ws_ingest_server.active_ui_websockets) >= 1
        with client.websocket_connect("/ws/dispatch") as ws2:
            assert len(ws_ingest_server.active_ui_websockets) >= 2
            # Verify both receive initial state
            m1 = json.loads(ws1.receive_text())
            m2 = json.loads(ws2.receive_text())
            assert m1["type"] == "INITIAL_QUEUE_STATE"
            assert m2["type"] == "INITIAL_QUEUE_STATE"

    # Both closed cleanly
    assert len(ws_ingest_server.active_ui_websockets) == 0

"""
Empirical Adversarial Stress Test Harness by Challenger 2
Stress tests:
1. compute_multimodal_triage under extreme corner cases (boundary V/A/D, zero/high jitter, instant override flips, NaN/inf).
2. Stoic shock paralysis evasion probing under acoustic & lexical permutations with fraud intent.
3. Performative yelling cap bypass probing under extreme acoustic loudness with zero fraud intent.
4. WebSocket dispatch queue under burst arrivals and rapid lien authorization (S4 -> S5).
5. High concurrency scalability and latency SLA verification.
"""

import math
import json
import sys
import os
import time
import asyncio
import numpy as np
from typing import Dict, Any, List

# Setup path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, os.path.join(CORE_DIR, "neuro-symbolic-triage"))
sys.path.insert(0, os.path.join(CORE_DIR, "semantic-asr-worker"))
sys.path.insert(0, os.path.join(CORE_DIR, "acoustic-ser-worker"))
sys.path.insert(0, os.path.join(CORE_DIR, "ingestion-gateway"))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from late_fusion_engine import compute_multimodal_triage, RAIL_DECAY_CONSTANTS
from pii_redaction_fst import extract_semantic_threat_score, scrub_pii_in_memory, CRITICAL_LEXICAL_VECTORS, OVERRIDE_TRIGGERS
from cfcfrms_jsonld_builder import build_cfcfrms_jsonld
import ws_ingest_server
from ws_ingest_server import app
from starlette.testclient import TestClient

def test_multimodal_triage_corner_cases():
    print("=" * 70)
    print("TEST 1: compute_multimodal_triage CORNER CASES & BOUNDARY CONDITIONS")
    print("=" * 70)
    
    results = []

    # 1.1 Boundary values of Arousal, Valence, Dominance
    v_a_d_cases = [
        ("Zero coordinates", 0.0, 0.0, 0.0, 1.0, 10.0, 0.1, 0.0, 0.0, False),
        ("Maximum normal coordinates", 1.0, 1.0, 1.0, 1.0, 10.0, 0.1, 0.0, 0.0, False),
        ("Negative coordinates", -1.0, -0.5, -0.5, 1.0, 10.0, 0.1, 0.0, 0.0, False),
        ("Extreme coordinates (> 1.0)", 2.5, 3.0, 2.0, 1.0, 10.0, 0.1, 0.0, 0.0, False),
    ]

    for label, val, aro, dom, jit, sig, spf, unc, sem, ovr in v_a_d_cases:
        try:
            res = compute_multimodal_triage(
                valence=val, arousal=aro, dominance=dom,
                jitter_pct=jit, sigma_f0_hz=sig, spoof_prob=spf,
                epistemic_uncertainty=unc, s_semantic=sem,
                override_active=ovr, matched_keywords=[]
            )
            score = res["urgency_score"]
            valid = 0.0 <= score <= 1.0
            print(f"[{'PASS' if valid else 'FAIL'}] {label}: U={score}, badge={res['badge']}, phi_vad={res.get('phi_vad')}, state={res['state']}")
            results.append((label, valid, f"U={score}"))
        except Exception as e:
            print(f"[FAIL-EXCEPTION] {label}: {e}")
            results.append((label, False, str(e)))

    # 1.2 Zero, high, infinite jitter
    jitter_cases = [
        ("Zero jitter (0.0%)", 0.0, 10.0),
        ("Micro jitter (0.001%)", 0.001, 10.0),
        ("Sub-threshold jitter (2.19%)", 2.19, 10.0),
        ("Threshold jitter (2.20%)", 2.20, 10.0),
        ("Super-threshold jitter (2.21%)", 2.21, 10.0),
        ("Massive pathological jitter (50.0%)", 50.0, 10.0),
        ("Negative jitter (-5.0%)", -5.0, 10.0),
    ]

    for label, jit, sig in jitter_cases:
        try:
            # performative screaming test (high arousal, zero fraud)
            res = compute_multimodal_triage(
                valence=0.3, arousal=0.85, dominance=0.7,
                jitter_pct=jit, sigma_f0_hz=sig, spoof_prob=0.05,
                epistemic_uncertainty=0.05, s_semantic=0.0,
                override_active=False, matched_keywords=[]
            )
            is_performative = res["performative_flag"]
            score = res["urgency_score"]
            print(f"  Jitter Test [{label}]: jit={jit} -> performative={is_performative}, U={score}, state={res['state']}")
        except Exception as e:
            print(f"  Jitter Test [FAIL-EXCEPTION] {label}: {e}")

    # 1.3 Instant override flips
    print("\n--- Instant Override Flips (Toggle Active/Inactive) ---")
    flip_seq = [False, True, False, True, True, False]
    scores = []
    for i, ovr in enumerate(flip_seq):
        res = compute_multimodal_triage(
            valence=0.2, arousal=0.2, dominance=0.2,
            jitter_pct=1.0, sigma_f0_hz=5.0, spoof_prob=0.05,
            epistemic_uncertainty=0.05, s_semantic=0.95,
            override_active=ovr, matched_keywords=["DIGITAL ARREST"]
        )
        scores.append((ovr, res["urgency_score"], res["badge"], res["state"]))
        print(f"  Step {i} (Override={ovr}): U={res['urgency_score']}, badge={res['badge']}, state={res['state']}")

    # 1.4 NaN and Infinity robustness
    print("\n--- NaN / Inf Stress Probing ---")
    nan_inf_cases = [
        ("NaN valence", float("nan"), 0.5, 0.5),
        ("Inf arousal", 0.5, float("inf"), 0.5),
        ("Negative Inf dominance", 0.5, 0.5, float("-inf")),
    ]
    for label, val, aro, dom in nan_inf_cases:
        try:
            res = compute_multimodal_triage(
                valence=val, arousal=aro, dominance=dom,
                jitter_pct=1.0, sigma_f0_hz=10.0, spoof_prob=0.05,
                epistemic_uncertainty=0.05, s_semantic=0.0,
                override_active=False, matched_keywords=[]
            )
            print(f"  [{label}]: U={res['urgency_score']}")
        except Exception as e:
            print(f"  [{label}]: Expected handled/exception -> {type(e).__name__}: {e}")

    # 1.5 Rail decay edge cases (negative or massive minutes, unknown rail)
    print("\n--- Rail Decay Edge Cases ---")
    rail_cases = [
        ("Zero minutes", 0.0, "RTGS"),
        ("Negative elapsed minutes (-10.0 min)", -10.0, "RTGS"),
        ("Massive elapsed minutes (10,000 min)", 10000.0, "RTGS"),
        ("Unknown payment rail", 8.0, "HAWALA"),
        ("Empty string payment rail", 8.0, ""),
    ]
    for label, mins, rail in rail_cases:
        try:
            res = compute_multimodal_triage(
                valence=0.2, arousal=0.2, dominance=0.2,
                jitter_pct=1.0, sigma_f0_hz=5.0, spoof_prob=0.05,
                epistemic_uncertainty=0.05, s_semantic=0.95,
                override_active=True, matched_keywords=["RTGS"],
                elapsed_txn_minutes=mins, detected_rail=rail
            )
            print(f"  [{label}]: p_freeze={res['p_freeze']}, state={res['state']}")
        except Exception as e:
            print(f"  [{label}]: Exception -> {e}")


def test_stoic_shock_evasion_probing():
    print("\n" + "=" * 70)
    print("TEST 2: STOIC SHOCK PARALYSIS GATE EVASION PROBING")
    print("=" * 70)

    # 2.1 Acoustic Boundary Probing around sigma_f0_hz=8.0 and arousal=0.35
    print("--- 2.1 Acoustic Boundary Perturbations with Fraud Intent ---")
    acoustic_boundary_cases = [
        ("Nominal stoic shock", 4.2, 0.19, True),
        ("Pitch right at boundary (7.99 Hz)", 7.99, 0.25, True),
        ("Pitch slightly above boundary (8.01 Hz)", 8.01, 0.25, True),
        ("Pitch significantly higher (12.0 Hz)", 12.0, 0.25, True),
        ("Arousal right at boundary (0.349)", 5.0, 0.349, True),
        ("Arousal slightly above boundary (0.351)", 5.0, 0.351, True),
        ("Arousal moderately higher (0.45)", 5.0, 0.45, True),
    ]

    for label, sig, aro, ovr in acoustic_boundary_cases:
        res = compute_multimodal_triage(
            valence=0.2, arousal=aro, dominance=0.2,
            jitter_pct=1.2, sigma_f0_hz=sig, spoof_prob=0.05,
            epistemic_uncertainty=0.08, s_semantic=0.95,
            override_active=ovr, matched_keywords=["DIGITAL ARREST", "RTGS"]
        )
        is_p1 = res["urgency_score"] >= 0.85
        badge_p1 = "PRIORITY-1" in res["badge"]
        is_s4 = res["state"] == "S4_LIEN_PAYLOAD_STAGED"
        print(f"  [{'PASS' if (is_p1 and is_s4) else 'FLAG'}] {label}: sig={sig}, aro={aro} -> U={res['urgency_score']}, shock_flag={res['shock_paralysis_flag']}, badge='{res['badge']}', state={res['state']}")

    # 2.2 Lexical Permutations Probing
    print("\n--- 2.2 Lexical Permutations with Genuinely Present Fraud Intent ---")
    lexical_cases = [
        ("Canonical Digital Arrest", "Sir mera digital arrest ho gaya hai 12 lakh rtgs karwa diya"),
        ("CBI Warrant & Account Emptied", "CBI warrant aaya tha mera account emptied ho gaya 50 lakh"),
        ("Suicide threat with financial fraud", "Mera poora paisa chala gaya suicide karne ja raha hoon"),
        # Sub-vectors in CRITICAL_LEXICAL_VECTORS but NOT in OVERRIDE_TRIGGERS:
        ("Customs & FedEx Parcel Scam", "Customs seized my fedex parcel narcotics bolkar cbi officer ne 5 lakh maanga"),
        ("CBI Officer & Life Threat", "Ek cbi officer ne call kiya life threat dekar upi se 2 lakh transfer karwaya"),
        ("UPI Phishing with OTP", "Unhone upi par otp maang kar paise nikaal liye"),
        # Paraphrased / spacing variations:
        ("Digital-Arrest hyphenated", "Sir mera digital-arrest ho gaya hai"),
        ("Giraftari (Hindi translation)", "Sir mera digital giraftari aur warrant dikhaya hai"),
        ("Pure digits without 'lakh' keyword", "Unhone mere 1200000 transfer karwa liye"),
    ]

    for label, text in lexical_cases:
        scrubbed = scrub_pii_in_memory(text)
        s_score, ovr_flag, matched = extract_semantic_threat_score(scrubbed)
        
        # Now pass to triage under stoic shock acoustic parameters (sig=4.5, aro=0.20)
        res = compute_multimodal_triage(
            valence=0.2, arousal=0.20, dominance=0.2,
            jitter_pct=1.2, sigma_f0_hz=4.5, spoof_prob=0.05,
            epistemic_uncertainty=0.08, s_semantic=s_score,
            override_active=ovr_flag, matched_keywords=matched
        )
        is_p1 = res["urgency_score"] >= 0.85
        is_s4 = res["state"] == "S4_LIEN_PAYLOAD_STAGED"
        print(f"  {'[PASS]' if (is_p1 and is_s4) else '[ALERT]'} {label}:")
        print(f"     s_score={s_score}, ovr_flag={ovr_flag}, matched={matched}")
        print(f"     U={res['urgency_score']}, shock_flag={res['shock_paralysis_flag']}, badge='{res['badge']}', state={res['state']}")


def test_performative_yelling_cap_bypass_probing():
    print("\n" + "=" * 70)
    print("TEST 3: PERFORMATIVE YELLING CAP BYPASS PROBING")
    print("=" * 70)

    # 3.1 Loudness Spikes with Zero Fraud Intent
    print("--- 3.1 Extreme Acoustic Volume Spikes (Zero Fraud Intent) ---")
    yelling_cases = [
        ("Nominal performative screaming", 0.85, 0.35, 0.78, 1.1),
        ("Max arousal (1.0) & low jitter", 1.0, 0.1, 0.9, 0.8),
        ("Arousal right below cap threshold (0.749)", 0.749, 0.3, 0.7, 1.2),
        ("Arousal right above cap threshold (0.751)", 0.751, 0.3, 0.7, 1.2),
        ("Loud scream with mic distortion/jitter (2.25%)", 0.90, 0.2, 0.8, 2.25),
        ("High jitter pathological tremor (3.5%)", 0.90, 0.2, 0.8, 3.5),
        ("Pure acoustic panic coords (V=0.0, D=0.0, A=0.74)", 0.74, 0.0, 0.0, 1.5),
        ("Pure acoustic panic coords (V=0.0, D=0.0, A=0.85, jit=2.3%)", 0.85, 0.0, 0.0, 2.3),
    ]

    for label, aro, val, dom, jit in yelling_cases:
        res = compute_multimodal_triage(
            valence=val, arousal=aro, dominance=dom,
            jitter_pct=jit, sigma_f0_hz=28.0, spoof_prob=0.04,
            epistemic_uncertainty=0.05, s_semantic=0.0,
            override_active=False, matched_keywords=[]
        )
        is_capped = res["urgency_score"] <= 0.45
        is_s4 = res["state"] == "S4_LIEN_PAYLOAD_STAGED"
        has_lien = res["cfcfrms_lien_draft"] is not None
        status = "PASS" if is_capped and not is_s4 and not has_lien else "ALERT"
        print(f"  [{status}] {label}:")
        print(f"     aro={aro}, jit={jit}, phi_vad={res.get('phi_vad')} -> U={res['urgency_score']}, capped={is_capped}, state={res['state']}, has_lien={has_lien}")


def test_websocket_dispatch_queue_stress():
    print("\n" + "=" * 70)
    print("TEST 4: WEBSOCKET DISPATCH QUEUE & BURST LIEN AUTHORIZATION")
    print("=" * 70)

    client = TestClient(app)

    # 4.1 Rapid Burst Arrivals & Queue Re-ranking
    print("--- 4.1 Rapid Queue Insertion & Re-ranking Under 100 Burst Calls ---")
    ws_ingest_server.initialize_default_queue()
    initial_len = len(ws_ingest_server.active_call_queue)
    print(f"  Initial queue size: {initial_len}")

    # Inject 100 synthetic burst streams with varying urgencies
    np.random.seed(42)
    burst_start = time.perf_counter()
    for i in range(100):
        urgency = round(float(np.random.uniform(0.10, 0.98)), 2)
        stream_id = f"burst-{i+1:03d}"
        ws_ingest_server.active_call_queue.append({
            "stream_id": stream_id,
            "caller_name": f"Burst Caller {i+1}",
            "phone_number": f"+91 98*** **{i:03d}",
            "wait_time_sec": int(np.random.randint(5, 120)),
            "loss_amount": f"₹{int(np.random.randint(1, 50))},00,000",
            "detected_rail": np.random.choice(["UPI", "IMPS", "RTGS"]),
            "urgency_score": urgency,
            "badge": "PRIORITY-1" if urgency >= 0.72 else "ROUTINE",
            "state": "S4_LIEN_PAYLOAD_STAGED" if urgency >= 0.85 else "S2_ACOUSTIC_LEXICAL_SURVEILLANCE",
            "spoof_prob": 0.05
        })

    # Sort queue descending (dynamic re-ranking)
    sort_start = time.perf_counter()
    ws_ingest_server.active_call_queue.sort(key=lambda x: x["urgency_score"], reverse=True)
    sort_duration_ms = (time.perf_counter() - sort_start) * 1000
    burst_total_ms = (time.perf_counter() - burst_start) * 1000

    print(f"  Injected 100 streams. Total queue size: {len(ws_ingest_server.active_call_queue)}")
    print(f"  Re-ranking sort time: {sort_duration_ms:.3f} ms (SLA < 18.0 ms)")
    print(f"  Total burst handling time: {burst_total_ms:.3f} ms")

    # Verify descending ordering invariant
    scores = [item["urgency_score"] for item in ws_ingest_server.active_call_queue]
    is_sorted_desc = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    print(f"  Descending queue order invariant: {'PASS' if is_sorted_desc else 'FAIL'} (Top U={scores[0]}, Bottom U={scores[-1]})")

    # 4.2 Rapid Burst Lien Authorization (S4 -> S5 transition)
    print("\n--- 4.2 Rapid Consecutive Lien Authorizations (S4 -> S5) ---")
    s4_streams = [item["stream_id"] for item in ws_ingest_server.active_call_queue if item["state"] == "S4_LIEN_PAYLOAD_STAGED"]
    print(f"  Found {len(s4_streams)} streams eligible for lien authorization in queue")

    auth_latencies = []
    auth_successes = 0
    for sid in s4_streams[:20]: # Authorize top 20 rapidly
        t0 = time.perf_counter()
        resp = client.post("/api/authorize-lien", json={"stream_id": sid})
        dt = (time.perf_counter() - t0) * 1000
        auth_latencies.append(dt)
        if resp.status_code == 200 and resp.json().get("status") == "SUCCESS":
            auth_successes += 1
            matched = next((c for c in ws_ingest_server.active_call_queue if c["stream_id"] == sid), None)
            if matched["state"] != "S5_LIEN_DISPATCHED_TO_NPCI":
                print(f"DEBUG: sid={sid}, resp={resp.json()}, matched_state={matched['state']}")
            assert matched["state"] == "S5_LIEN_DISPATCHED_TO_NPCI"
            assert matched.get("lien_pushed") is True
        else:
            print(f"DEBUG: sid={sid}, status={resp.status_code}, body={resp.text}")

    print(f"  Rapid Authorizations: {auth_successes}/20 succeeded")
    print(f"  Latency P50: {np.percentile(auth_latencies, 50):.3f} ms, Max: {np.max(auth_latencies):.3f} ms")

    # 4.3 Concurrent WebSocket Connections & Teardown under Stress
    print("\n--- 4.3 WebSocket /ws/dispatch Stress & Message Delivery ---")
    with client.websocket_connect("/ws/dispatch") as ws1:
        init_msg = json.loads(ws1.receive_text())
        assert init_msg["type"] == "INITIAL_QUEUE_STATE"
        
        # Test stream selection
        ws1.send_text(json.dumps({"action": "SELECT_STREAM", "stream_id": "106"}))
        select_msg = json.loads(ws1.receive_text())
        assert select_msg["type"] == "STREAM_SELECTED"
        print(f"  WebSocket single client interactive command: PASS")

    # Re-initialize default queue
    ws_ingest_server.initialize_default_queue()


def test_concurrency_load_and_latency_sla():
    print("\n" + "=" * 70)
    print("TEST 5: HIGH CONCURRENCY SCALABILITY (>= 50 STREAMS) & LATENCY SLA")
    print("=" * 70)

    from concurrent.futures import ThreadPoolExecutor

    def simulate_call_stream(stream_idx: int) -> float:
        """Simulates full audio chunk processing: VAD -> SER -> ASR -> Late Fusion -> UI payload."""
        t_start = time.perf_counter()
        
        # 1. Ingest simulated 20ms frame (640 bytes)
        frame = np.random.uniform(-0.1, 0.1, 320).astype(np.float32)
        
        # 2. VAD check
        is_speech = True
        
        # 3. Simulated SER (Wiener-Khinchin FFT autocorrelation on 1.5s window)
        audio_window = np.random.uniform(-0.2, 0.2, 24000).astype(np.float32)
        n = len(audio_window)
        n_fft = 2 ** int(np.ceil(np.log2(2 * n - 1)))
        fx = np.fft.rfft(audio_window, n=n_fft)
        corr = np.fft.irfft(fx.real**2 + fx.imag**2, n=n_fft)[:n]
        
        # 4. Simulated ASR + PII scrub
        raw_text = f"Sir mera CBI digital arrest ho gaya hai complaint number {stream_idx} aadhaar 9844 2109 8832 otp 492104"
        scrubbed = scrub_pii_in_memory(raw_text)
        s_score, ovr, kws = extract_semantic_threat_score(scrubbed)
        
        # 5. Late fusion
        triage = compute_multimodal_triage(
            valence=0.2, arousal=0.25, dominance=0.2,
            jitter_pct=1.4, sigma_f0_hz=5.2, spoof_prob=0.05,
            epistemic_uncertainty=0.08, s_semantic=s_score,
            override_active=ovr, matched_keywords=kws
        )
        
        # Glass-to-glass latency
        dt_ms = (time.perf_counter() - t_start) * 1000
        # Add telecom chunk delivery offset (nominal 20ms) and model inference budget (nominal ASR 115ms)
        total_g2g_ms = dt_ms + 20.0 + 115.0
        return total_g2g_ms

    for concurrency in [10, 25, 50, 75]:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            latencies = list(executor.map(simulate_call_stream, range(concurrency)))
        
        p50 = float(np.percentile(latencies, 50))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))
        max_lat = float(np.max(latencies))
        
        passed = max_lat < 800.0 and p50 <= 450.0 and p99 <= 600.0
        print(f"  Concurrency Tier {concurrency:2d} streams: P50={p50:6.2f}ms | P95={p95:6.2f}ms | P99={p99:6.2f}ms | Max={max_lat:6.2f}ms [{'PASS' if passed else 'FAIL'}]")


if __name__ == "__main__":
    test_multimodal_triage_corner_cases()
    test_stoic_shock_evasion_probing()
    test_performative_yelling_cap_bypass_probing()
    test_websocket_dispatch_queue_stress()
    test_concurrency_load_and_latency_sla()

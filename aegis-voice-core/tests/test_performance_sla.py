"""
Automated Pytest Suite for Milestone 4 (R3):
Pipeline Latency Profiling, Concurrency Load Testing, Storage SLA & Verification Runner

Asserts:
1. Individual Stage Execution Latencies:
   - Ingestion Gateway          <= 25.0 ms
   - Silero VAD                  <=  2.0 ms
   - Acoustic SER                <= 25.0 ms
   - Semantic ASR + PII Scrubber <= 125.0 ms
   - Neuro-Symbolic Late Fusion  <=  5.0 ms
   - UI Telemetry & Render       <= 18.0 ms
   - Nominal Budget Sum          <= 200.0 ms (< 800.0 ms SLA)

2. Multi-Stream Concurrency Load Testing (10, 25, 50 concurrent streams):
   - Glass-to-glass latency P50 <= 450.0 ms
   - Glass-to-glass latency P99 <= 600.0 ms
   - Glass-to-glass latency Max strictly < 800.0 ms

3. DPDP Act 2023 & UIDAI Zero-Disk Storage Invariant:
   - Zero .wav or .pcm files persisted to disk.
   - In-memory volatile RAM ring buffers only.

4. Artifact Compliance & Master Verification Runner:
   - Schema and status of aegis-voice-core/profiling_results.json.
   - Programmatic execution of run_pipeline_profiling.py and run_verification.py.
"""

import os
import sys
import glob
import json
import time
import pytest
import numpy as np

# Ensure microservice directories are discoverable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SCRIPTS_DIR = os.path.join(CORE_DIR, "scripts")

for sub in ["semantic-asr-worker", "acoustic-ser-worker", "neuro-symbolic-triage", "ingestion-gateway", "telephony-bridge", "scripts"]:
    p = os.path.join(CORE_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from shm_ring_buffer import EphemeralAudioRingBuffer
from vad_denoiser_router import SileroVADRouter
from opensmile_egemaps_fallback import FastAcousticBiomarkerExtractor
from emotion2vec_trt_runner import Emotion2VecRunner
from indic_conformer_ctc import IndicConformerStreamWorker
from pii_redaction_fst import scrub_pii_in_memory, extract_semantic_threat_score
from late_fusion_engine import compute_multimodal_triage

from run_pipeline_profiling import (
    profile_stage_1_ingestion,
    profile_stage_2_silero_vad,
    profile_stage_3_acoustic_ser,
    profile_stage_4_semantic_asr_pii,
    profile_stage_5_late_fusion,
    profile_stage_6_ui_telemetry,
    profile_all_individual_stages,
    run_concurrency_load_benchmark,
    audit_zero_disk_storage_invariants,
    run_all_profiling
)
from run_verification import run_full_verification


# ==============================================================================
# 1. INDIVIDUAL STAGE LATENCY SLA TESTS
# ==============================================================================

def test_stage_1_ingestion_gateway_latency_budget():
    """Verify Ingestion Gateway satisfies the <= 25.0ms SLA budget."""
    res = profile_stage_1_ingestion(iterations=100)
    assert res["passed"] is True, f"Ingestion SLA failed: p95={res['measured_p95_ms']}ms, mean={res['measured_mean_ms']}ms"
    assert res["measured_p95_ms"] <= 25.0, f"P95 latency {res['measured_p95_ms']}ms exceeded 25.0ms SLA"
    assert res["measured_mean_ms"] <= 25.0, f"Mean latency {res['measured_mean_ms']}ms exceeded 25.0ms SLA"
    assert res["ram_push_mean_ms"] < 1.0, f"Pure RAM buffer push took too long: {res['ram_push_mean_ms']}ms"
    assert res["status"] == "PASSED"


def test_stage_2_silero_vad_latency_budget():
    """Verify Silero VAD satisfies the <= 2.0ms SLA budget."""
    res = profile_stage_2_silero_vad(iterations=100)
    assert res["passed"] is True, f"Silero VAD SLA failed: p95={res['measured_p95_ms']}ms, mean={res['measured_mean_ms']}ms"
    assert res["measured_p95_ms"] <= 2.0, f"P95 latency {res['measured_p95_ms']}ms exceeded 2.0ms SLA"
    assert res["measured_mean_ms"] <= 2.0, f"Mean latency {res['measured_mean_ms']}ms exceeded 2.0ms SLA"
    assert res["status"] == "PASSED"


def test_stage_3_acoustic_ser_latency_budget():
    """Verify Acoustic SER satisfies the <= 25.0ms SLA budget with FFT autocorrelation."""
    res = profile_stage_3_acoustic_ser(iterations=30)
    assert res["passed"] is True, f"Acoustic SER SLA failed: p95={res['measured_p95_ms']}ms, mean={res['measured_mean_ms']}ms"
    assert res["measured_p95_ms"] <= 25.0, f"P95 latency {res['measured_p95_ms']}ms exceeded 25.0ms SLA"
    assert res["measured_mean_ms"] <= 25.0, f"Mean latency {res['measured_mean_ms']}ms exceeded 25.0ms SLA"
    assert res["status"] == "PASSED"


def test_stage_4_semantic_asr_pii_latency_budget():
    """Verify Semantic ASR + PII Scrubber satisfies <= 125.0ms and PII scrub < 1.8ms."""
    res = profile_stage_4_semantic_asr_pii(iterations=100)
    assert res["passed"] is True, f"Semantic ASR+PII SLA failed: p95={res['measured_p95_ms']}ms, mean={res['measured_mean_ms']}ms"
    assert res["measured_p95_ms"] <= 125.0, f"P95 latency {res['measured_p95_ms']}ms exceeded 125.0ms SLA"
    assert res["measured_mean_ms"] <= 125.0, f"Mean latency {res['measured_mean_ms']}ms exceeded 125.0ms SLA"
    assert res["pii_scrubber_p99_ms"] < 1.8, f"PII scrubber P99 {res['pii_scrubber_p99_ms']}ms exceeded 1.8ms statutory limit"
    assert res["status"] == "PASSED"


def test_stage_5_late_fusion_latency_budget():
    """Verify Neuro-Symbolic Late Fusion satisfies the <= 5.0ms SLA budget."""
    res = profile_stage_5_late_fusion(iterations=100)
    assert res["passed"] is True, f"Late Fusion SLA failed: p95={res['measured_p95_ms']}ms, mean={res['measured_mean_ms']}ms"
    assert res["measured_p95_ms"] <= 5.0, f"P95 latency {res['measured_p95_ms']}ms exceeded 5.0ms SLA"
    assert res["measured_mean_ms"] <= 5.0, f"Mean latency {res['measured_mean_ms']}ms exceeded 5.0ms SLA"
    assert res["status"] == "PASSED"


def test_stage_6_ui_telemetry_latency_budget():
    """Verify UI Telemetry & Render satisfies the <= 18.0ms SLA budget."""
    res = profile_stage_6_ui_telemetry(iterations=100)
    assert res["passed"] is True, f"UI Telemetry SLA failed: p95={res['measured_p95_ms']}ms, mean={res['measured_mean_ms']}ms"
    assert res["measured_p95_ms"] <= 18.0, f"P95 latency {res['measured_p95_ms']}ms exceeded 18.0ms SLA"
    assert res["measured_mean_ms"] <= 18.0, f"Mean latency {res['measured_mean_ms']}ms exceeded 18.0ms SLA"
    assert res["pure_render_mean_ms"] < 1.0, f"Pure render/sort took too long: {res['pure_render_mean_ms']}ms"
    assert res["status"] == "PASSED"


def test_nominal_stage_budget_sum_within_sla():
    """Verify the sum of nominal stage budgets (200.0ms) is strictly within statutory 800.0ms SLA."""
    all_stages = profile_all_individual_stages(iterations=50)
    assert all_stages["all_stages_passed"] is True
    assert all_stages["nominal_budget_sum_ms"] <= 200.0, (
        f"Nominal budget sum {all_stages['nominal_budget_sum_ms']}ms exceeded 200.0ms"
    )
    assert all_stages["measured_mean_sum_ms"] < 800.0, (
        f"Measured stage sum {all_stages['measured_mean_sum_ms']}ms violated 800.0ms SLA"
    )
    assert all_stages["within_sla_limit"] is True


# ==============================================================================
# 2. CONCURRENCY LOAD TESTING PERCENTILES
# ==============================================================================

def test_concurrency_load_10_streams():
    """Verify 10 concurrent streams satisfy P50 <= 450ms, P99 <= 600ms, Max < 800ms."""
    bench = run_concurrency_load_benchmark(concurrency_levels=[10], repeats_per_stream=2)
    tier = bench["concurrency_benchmarks"]["concurrency_10"]
    assert tier["status"] == "PASSED"
    assert tier["p50_passed"] is True, f"P50 {tier['measured_p50_ms']}ms exceeded 450.0ms"
    assert tier["p99_passed"] is True, f"P99 {tier['measured_p99_ms']}ms exceeded 600.0ms"
    assert tier["max_passed"] is True, f"Max {tier['measured_max_ms']}ms violated 800.0ms SLA"


def test_concurrency_load_25_streams():
    """Verify 25 concurrent streams satisfy P50 <= 450ms, P99 <= 600ms, Max < 800ms."""
    bench = run_concurrency_load_benchmark(concurrency_levels=[25], repeats_per_stream=2)
    tier = bench["concurrency_benchmarks"]["concurrency_25"]
    assert tier["status"] == "PASSED"
    assert tier["p50_passed"] is True, f"P50 {tier['measured_p50_ms']}ms exceeded 450.0ms"
    assert tier["p99_passed"] is True, f"P99 {tier['measured_p99_ms']}ms exceeded 600.0ms"
    assert tier["max_passed"] is True, f"Max {tier['measured_max_ms']}ms violated 800.0ms SLA"


def test_concurrency_load_50_streams():
    """Verify 50 concurrent streams satisfy P50 <= 450ms, P99 <= 600ms, Max < 800ms."""
    bench = run_concurrency_load_benchmark(concurrency_levels=[50], repeats_per_stream=2)
    tier = bench["concurrency_benchmarks"]["concurrency_50"]
    assert tier["status"] == "PASSED"
    assert tier["p50_passed"] is True, f"P50 {tier['measured_p50_ms']}ms exceeded 450.0ms"
    assert tier["p99_passed"] is True, f"P99 {tier['measured_p99_ms']}ms exceeded 600.0ms"
    assert tier["max_passed"] is True, f"Max {tier['measured_max_ms']}ms violated 800.0ms SLA"


# ==============================================================================
# 3. DPDP ACT 2023 ZERO-DISK INVARIANT AUDIT
# ==============================================================================

def test_dpdp_zero_disk_storage_invariant():
    """Verify zero .wav/.pcm/.raw audio bytes written to disk under DPDP Act 2023."""
    audit = audit_zero_disk_storage_invariants(search_root=CORE_DIR)
    assert audit["dpdp_compliant"] is True
    assert audit["status"] == "PASSED"
    assert audit["total_audio_files_on_disk"] == 0, f"Found {audit['total_audio_files_on_disk']} audio files on disk!"
    assert audit["total_audio_bytes_on_disk"] == 0
    assert audit["zero_disk_persistence_invariant"] == "VERIFIED_TMPFS_VOLATILE_ONLY"


# ==============================================================================
# 4. PROFILING RESULTS JSON & VERIFICATION RUNNER
# ==============================================================================

def test_profiling_results_json_schema_and_artifacts():
    """Verify aegis-voice-core/profiling_results.json exists, valid schema, all SLAs passed."""
    json_path = os.path.join(CORE_DIR, "profiling_results.json")
    if not os.path.exists(json_path):
        run_all_profiling(concurrency_levels=[10, 25, 50], stage_iterations=50, verbose=False)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "concurrency_50" not in data.get("concurrency_benchmarks", {}):
        data, _ = run_all_profiling(concurrency_levels=[10, 25, 50], stage_iterations=50, verbose=False)

    meta = data["profiling_metadata"]
    assert meta["overall_status"] == "ALL_SLAS_PASSED"
    assert meta["sla_compliance"] == "FULL_SLA_COMPLIANCE"
    assert meta["dpdp_compliance"] == "DPDP_2023_ZERO_DISK_CERTIFIED"

    stages = data["stage_latency_profiles"]
    assert len(stages) == 6
    for stage_key, s in stages.items():
        assert s["status"] == "PASSED", f"Stage {stage_key} failed in JSON artifact"
        assert s["measured_p95_ms"] <= s["sla_target_ms"]
        assert s["measured_mean_ms"] <= s["sla_target_ms"]

    concur = data["concurrency_benchmarks"]
    for c_key in ["concurrency_10", "concurrency_25", "concurrency_50"]:
        assert c_key in concur
        assert concur[c_key]["status"] == "PASSED"

    g2g = data["glass_to_glass_summary"]
    assert g2g["overall_p50_ms"] <= 450.0
    assert g2g["overall_p99_ms"] <= 600.0
    assert g2g["overall_max_ms"] < 800.0


def test_run_pipeline_profiling_programmatic_execution():
    """Verify run_all_profiling executes cleanly and returns exit code 0."""
    data, exit_code = run_all_profiling(
        concurrency_levels=[10, 25, 50],
        stage_iterations=30,
        verbose=False
    )
    assert exit_code == 0
    assert data["profiling_metadata"]["overall_status"] == "ALL_SLAS_PASSED"


def test_run_verification_master_programmatic_execution(monkeypatch):
    """Verify run_full_verification executes all 4 pillars and returns exit code 0."""
    from run_verification import (
        execute_step_2_adversarial_benchmark,
        execute_step_3_pipeline_profiling_sla,
        execute_step_4_dpdp_zero_disk_audit,
        run_full_verification
    )
    # Direct genuine execution of pillars 2, 3, 4
    s2 = execute_step_2_adversarial_benchmark()
    assert s2["passed"] is True
    s3 = execute_step_3_pipeline_profiling_sla()
    assert s3["passed"] is True
    s4 = execute_step_4_dpdp_zero_disk_audit()
    assert s4["passed"] is True

    # Prevent nested pytest fork bomb while testing master orchestration
    monkeypatch.setattr(
        "run_verification.execute_step_1_automated_test_suite",
        lambda verbose=False: {
            "step_id": 1,
            "name": "Comprehensive Multi-Service Test Suite (pytest)",
            "passed": True,
            "status": "PASSED",
            "exit_code": 0,
            "duration_sec": 0.01,
            "summary": "80+ passed in 2.5s"
        }
    )
    data, exit_code = run_full_verification(verbose=False)
    assert exit_code == 0
    assert data["verification_metadata"]["overall_status"] == "ALL_ACCEPTANCE_CRITERIA_PASSED"
    assert data["verification_metadata"]["certification"] == "PRODUCTION_CERTIFIED_READY_FOR_DISPATCH"
    assert data["verification_metadata"]["all_steps_passed"] is True
    pillars = data["pillars"]
    assert pillars["pillar_1_multi_service_tests"]["passed"] is True
    assert pillars["pillar_2_adversarial_benchmarks"]["passed"] is True
    assert pillars["pillar_3_latency_profiling_sla"]["passed"] is True
    assert pillars["pillar_4_dpdp_zero_disk_audit"]["passed"] is True

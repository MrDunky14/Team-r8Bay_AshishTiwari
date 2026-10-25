# Dispatch for Worker M4

## Objective
Implement Milestone 4: Pipeline Profiling, Concurrency Load Testing, Latency Optimization, and One-Click Verification CLI Runner (R3).

## Target Files to Create
- `aegis-voice-core/scripts/run_pipeline_profiling.py`:
  - Profile individual execution latencies across all 6 pipeline stages:
    - Ingestion Gateway <= 25ms
    - Silero VAD <= 2ms
    - Acoustic SER <= 25ms
    - Semantic ASR + PII Scrubber <= 125ms
    - Neuro-Symbolic Late Fusion <= 5ms
    - UI Telemetry & Render <= 18ms
  - Multi-stream concurrency load testing:
    - Simulate 10-50 concurrent calls/streams.
    - Measure glass-to-glass latency distribution: P50 <= 450ms, P99 <= 600ms, Max < 800ms SLA.
  - Storage & memory invariant audit:
    - Confirm zero `.wav` or `.pcm` audio bytes written to disk during high-throughput execution.
  - Output structured JSON to `aegis-voice-core/profiling_results.json`.
- `aegis-voice-core/scripts/run_verification.py`:
  - One-click master CLI runner for continuous verification executing:
    1. Comprehensive Multi-Service Test Suite (pytest)
    2. Deterministic Adversarial Benchmark (5 scenarios & statistical gates)
    3. Performance SLA & Latency Profiling
    4. DPDP Zero-Disk Invariant Check
  - Returns exit code 0 if and only if all acceptance criteria pass.
- `aegis-voice-core/tests/test_performance_sla.py`:
  - Automated tests asserting all R3 SLA latency budgets, concurrency percentiles, and zero-disk storage invariants.

## Input Context
- `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\ORIGINAL_REQUEST.md`
- `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\orchestrator_1\PROJECT.md`
- Previous handoffs: `worker_m1/handoff.md`, `test_writer_m2/handoff.md`, `worker_m3/handoff.md`

## Acceptance Criteria
- Individual stage latency budgets verified (Ingestion <=25ms, VAD <=2ms, SER <=25ms, ASR+PII <=125ms, Late Fusion <=5ms, UI <=18ms).
- Concurrency load latency verified (P50 <=450ms, P99 <=600ms, max <800ms).
- Zero audio bytes written to disk confirmed.
- One-click runner `python aegis-voice-core/scripts/run_verification.py` executes cleanly with exit code 0.
- All tests pass under `pytest`.

## Output
Write report to `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m4\handoff.md`.


## 2026-10-25T07:01:46Z
From: 29f28c96-5ee8-41ee-b393-bf680b5f3bd1 (Orchestrator)
Content:
You are Worker M4 for Project Aegis-Voice.
Your assigned working directory is:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m4

Scope & Ownership:
You exclusively own:
- `aegis-voice-core/scripts/run_pipeline_profiling.py`
- `aegis-voice-core/scripts/run_verification.py`
- `aegis-voice-core/tests/test_performance_sla.py`
- `aegis-voice-core/profiling_results.json`

Key Tasks:
1. `run_pipeline_profiling.py`:
   - Profile individual execution latencies across all 6 pipeline stages:
     - Ingestion Gateway <= 25ms
     - Silero VAD <= 2ms
     - Acoustic SER <= 25ms
     - Semantic ASR + PII Scrubber <= 125ms
     - Neuro-Symbolic Late Fusion <= 5ms
     - UI Telemetry & Render <= 18ms
   - Concurrency load testing:
     - Simulate 10-50 concurrent calls/streams.
     - Measure glass-to-glass latency distribution: P50 <= 450ms, P99 <= 600ms, Max strictly < 800ms SLA.
   - Storage & memory invariant audit:
     - Verify zero `.wav` or `.pcm` audio bytes written to disk during high-throughput execution.
   - Output structured JSON to `aegis-voice-core/profiling_results.json`.
2. `run_verification.py`:
   - One-click master CLI runner executing:
     1. Comprehensive Multi-Service Test Suite (`pytest aegis-voice-core/tests`)
     2. Deterministic Adversarial Benchmark (`run_adversarial_benchmark.py`)
     3. Pipeline Profiling & SLA Verification (`run_pipeline_profiling.py`)
     4. DPDP Zero-Disk Invariant Check
   - Returns exit code 0 if all acceptance criteria pass.
3. `tests/test_performance_sla.py`:
   - Automated tests asserting all R3 SLA latency budgets, concurrency percentiles, and zero-disk storage invariants under pytest.

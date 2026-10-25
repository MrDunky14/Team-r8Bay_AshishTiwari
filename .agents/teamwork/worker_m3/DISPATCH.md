# Dispatch for Worker M3

## Objective
Implement Milestone 3: Deterministic Benchmark Evaluation & Adversarial Stress Validation across all 5 core edge-case scenarios required by R2.

## Target Files to Create
- `aegis-voice-core/scripts/run_adversarial_benchmark.py`: Standalone CLI benchmark suite executing all 5 adversarial scenarios, outputting structured JSON results to `aegis-voice-core/benchmark_results.json`.
- `aegis-voice-core/tests/test_adversarial_benchmarks.py`: Pytest suite verifying all 5 adversarial scenarios with 100% pass rate.
- `aegis-voice-core/benchmark_results.json`: Output results artifact.

## Scenarios to Implement & Verify
1. **Stoic Victim / Shock Paralysis**:
   - Flat pitch variance ($\sigma_{F_0} < 8\text{ Hz}$, e.g. 4.2Hz), low arousal ($A < 0.35$, e.g. 0.19).
   - Cybercrime intent ("digital arrest", "rtgs transfer", "cbi warrant").
   - Verification: Activates Semantic Floor, receives Priority-1 badge, urgency $U \ge 0.85$, state transitions to `S4_LIEN_PAYLOAD_STAGED`.
2. **Performative Screaming / Yelling**:
   - High loudness (>80dB, Arousal $A > 0.75$, e.g. 0.85), normal jitter (<2.2%, e.g. 1.1%), zero fraud intent ($S_{\text{sem}} = 0.0$).
   - Verification: Urgency strictly capped at Routine ($U \le 0.45$, e.g. 0.41), badge `AGITATED - NON-CRITICAL (ROUTINE)`.
3. **Synthetic Deepfake Spoof**:
   - AASIST-L phase entropy anomaly ($P_{\text{spoof}} > 0.70$, e.g. 0.94).
   - Verification: Immediately suppressed to $U = 0.15$, badge `SYNTHETIC SPOOF - BLOCKED`, queue escalation blocked.
4. **Frontier 1 Scammer-in-the-Background Coercion**:
   - Secondary laptop transducer roll-off (<280Hz) and bimodal coaching turn-taking micro-pauses (1.1s - 2.4s, e.g. 1.65s).
   - Verification: `coercion_detected == True`, transducer ratio $> 10$, coached pause detected.
5. **Silent Shadow Mode Statistical Gates**:
   - Multi-call evaluation verifying the 3 statutory gates:
     - Golden-Hour fraud recall >= 94.0%
     - False Positive Rate <= 8.5%
     - Mean Early Lead-Time Advantage >= 110s
   - Verification: All 3 gates passed, production status is `GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI`.

## Execution & Acceptance
- Run `python aegis-voice-core/scripts/run_adversarial_benchmark.py` and inspect `benchmark_results.json`.
- Run `pytest aegis-voice-core/tests/test_adversarial_benchmarks.py` and ensure 100% pass rate.
- Write report to `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m3\handoff.md`.


## 2026-10-25T06:52:36Z
[Message] timestamp=2026-10-25T06:52:36Z sender=29f28c96-5ee8-41ee-b393-bf680b5f3bd1 priority=MESSAGE_PRIORITY_HIGH content=You are Worker M3 for Project Aegis-Voice.
Your assigned working directory is:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m3

Mandatory requirements:
1. Read the verbatim user request at:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\ORIGINAL_REQUEST.md

2. Read your task dispatch at:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m3\DISPATCH.md

3. Read the project scope document:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\orchestrator_1\PROJECT.md

4. Read the survey and handoff reports:
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_3\handoff.md
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m1\handoff.md
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\test_writer_m2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Ownership:
You exclusively own:
- `aegis-voice-core/scripts/run_adversarial_benchmark.py`
- `aegis-voice-core/tests/test_adversarial_benchmarks.py`
- `aegis-voice-core/benchmark_results.json`

Key Tasks:
Build the deterministic benchmark evaluation & adversarial stress validation runner and test suite (R2) covering all 5 scenarios:
1. Stoic Victim / Shock Paralysis: flat pitch variance (sigma_F0 < 8Hz), low arousal (<0.35), high-value cybercrime intent -> Priority-1 (U >= 0.85, badge PRIORITY-1 [SHOCK / DISSOCIATION TRIAGE], state S4).
2. Performative Screaming / Yelling: high loudness (>80dB, arousal > 0.75), normal jitter (<2.2%), zero fraud intent -> capped at Routine (U <= 0.45, badge AGITATED - NON-CRITICAL (ROUTINE)).
3. Synthetic Deepfake Spoof: AASIST-L phase entropy anomaly (P_spoof > 0.70) -> immediately suppressed to U = 0.15, badge SYNTHETIC SPOOF - BLOCKED, queue escalation blocked.
4. Frontier 1 Scammer-in-the-Background Coercion: secondary laptop transducer roll-off (<280Hz) + bimodal coaching turn-taking micro-pauses (1.1s - 2.4s) -> coercion detected flag.
5. Silent Shadow Mode Statistical Gates: evaluation across simulated cohort verifying Golden-Hour recall >= 94.0%, False Positive Rate <= 8.5%, Lead-Time advantage >= 110s, status GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI.

Verification:
- Execute `python aegis-voice-core/scripts/run_adversarial_benchmark.py` and inspect generated `benchmark_results.json`.
- Execute `pytest aegis-voice-core/tests/test_adversarial_benchmarks.py` and confirm 100% pass rate.
- Write a detailed handoff report to:
`k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m3\handoff.md`
- Send message to orchestrator (Recipient: 29f28c96-5ee8-41ee-b393-bf680b5f3bd1) with evaluation results.

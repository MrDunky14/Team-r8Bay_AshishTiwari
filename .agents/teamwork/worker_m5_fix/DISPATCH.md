# Dispatch for Worker M5_Fix

## Objective
Implement all remediations and hardenings requested by Reviewer 1, Challenger 1, and Challenger 2:

1. **PII Scrubber Hardening (`aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py`)**:
   - Add `"oh": "0"` to `SPOKEN_DIGIT_MAP`.
   - Update digit collapsing regex to handle punctuation/whitespace: `re.sub(r'(?<=\d)[\s,.-]+(?=\d)', '', text)` so comma/hyphen separated spoken digits collapse into contiguous numbers.
   - Update `OTP_CONTEXT_PATTERN` to be bidirectional: match both `"otp is 492104"` and `"492104 was the otp"` / `"492104 otp"`.
   - Add spaced PAN normalization or pattern to catch `"A B C D E 1 2 3 4 F"`.
   - Expand `OVERRIDE_TRIGGERS` to include cybercrime modalities: `"upi"`, `"otp"`, `"customs"`, `"fedex"`, `"parcel"`, `"seized"`, `"aadhaar block"`, `"cyber"`, `"bank account emptied"`.

2. **Late Fusion Engine Hardening (`aegis-voice-core/neuro-symbolic-triage/late_fusion_engine.py`)**:
   - Compute `phi_vad`, `s_acoustic`, and `s_semantic` before early return gates, and include `"phi_vad"`, `"s_acoustic"`, and `"s_semantic"` in all return dictionaries (including deepfake suppression and performative yelling).
   - Ensure lower-bound clamping for urgency: `u_score = max(0.0, min(1.0, ...))`.
   - In S4 lien staging, require corroborating cyber fraud evidence: `if (override_active or (phi_vad > 0.30 and s_semantic > 0.0) or len(threat_vectors) > 0) and p_freeze >= 0.50:` preventing pure acoustic panic on medical/fire emergencies from drafting banking liens.

3. **AASIST-L Silence Gating (`aegis-voice-core/acoustic-ser-worker/aasist_spoof_guard.py`)**:
   - Check audio energy: if `rms < 1e-4` or max amplitude < 1e-4, return `is_spoofed=False, spoof_prob=0.0` (silence is not synthetic deepfake speech).

4. **Profiler Stability & Percentile SLA Check (`aegis-voice-core/scripts/run_pipeline_profiling.py` & `aegis-voice-core/tests/test_performance_sla.py`)**:
   - Update stage SLA checks to evaluate `p95_ms <= sla_budget` and `mean_ms <= sla_budget` rather than single-iteration raw `max_ms` to prevent Windows OS thread context-switching spikes from poisoning `profiling_results.json`.
   - Run `python aegis-voice-core/scripts/run_verification.py` repeatedly to verify 100% stable pass rate.

## Verification
- Run `pytest aegis-voice-core` and ensure 100% of tests pass.
- Run `python aegis-voice-core/scripts/run_verification.py` and verify exit code 0.
- Write handoff report to:
`k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m5_fix\handoff.md`.

## 2026-10-25T07:30:26Z
[Message from Orchestrator 29f28c96-5ee8-41ee-b393-bf680b5f3bd1]
You are Worker M5_Fix for Project Aegis-Voice.
Your assigned working directory is:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m5_fix

Mandatory requirements:
1. Read the verbatim user request at:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\ORIGINAL_REQUEST.md

2. Read your task dispatch at:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m5_fix\DISPATCH.md

3. Read the feedback from Reviewer 1, Challenger 1, and Challenger 2:
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\reviewer_1\handoff.md
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\challenger_1\handoff.md
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\challenger_2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Tasks:
1. `pii_redaction_fst.py`:
   - Add `"oh": "0"` to `SPOKEN_DIGIT_MAP`.
   - Update digit collapsing regex to handle punctuation/whitespace: `re.sub(r'(?<=\d)[\s,.-]+(?=\d)', '', text)`.
   - Update `OTP_CONTEXT_PATTERN` to be bidirectional: match both `"otp is 492104"` and `"492104 was the otp"` / `"492104 otp"`.
   - Add spaced PAN normalization or pattern to catch `"A B C D E 1 2 3 4 F"`.
   - Expand `OVERRIDE_TRIGGERS` to include cybercrime modalities: `"upi"`, `"otp"`, `"customs"`, `"fedex"`, `"parcel"`, `"seized"`, `"aadhaar block"`, `"cyber"`, `"bank account emptied"`.
2. `late_fusion_engine.py`:
   - Compute `phi_vad`, `s_acoustic`, and `s_semantic` before early return gates, and include `"phi_vad"`, `"s_acoustic"`, and `"s_semantic"` in all return dictionaries (including deepfake suppression and performative yelling).
   - Ensure lower-bound clamping for urgency: `u_score = max(0.0, min(1.0, ...))`.
   - In S4 lien staging, require corroborating cyber fraud evidence: `if (override_active or (phi_vad > 0.30 and s_semantic > 0.0) or len(threat_vectors) > 0) and p_freeze >= 0.50:` preventing pure acoustic panic on medical/fire emergencies from drafting banking liens.
3. `aasist_spoof_guard.py`:
   - Check audio energy: if `rms < 1e-4` or max amplitude < 1e-4, return `is_spoofed=False, spoof_prob=0.0` (silence is not synthetic deepfake speech).
4. `run_pipeline_profiling.py` & `test_performance_sla.py`:
   - Update stage SLA checks to evaluate `p95_ms <= sla_budget` and `mean_ms <= sla_budget` rather than single-iteration raw `max_ms` to prevent Windows OS thread context-switching spikes from causing false failures.
   - Run `python aegis-voice-core/scripts/run_verification.py` repeatedly to verify 100% stable pass rate.

Verification:
- Run `pytest aegis-voice-core` and verify 100% pass rate.
- Run `python aegis-voice-core/scripts/run_verification.py` and verify exit code 0.
- Write handoff report to:
`k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m5_fix\handoff.md`.
- Send message to orchestrator (Recipient: 29f28c96-5ee8-41ee-b393-bf680b5f3bd1) with your results.

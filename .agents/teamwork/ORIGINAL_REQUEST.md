# Original User Request

## 2026-10-25T06:16:24Z

Perform comprehensive automated testing, adversarial evaluation, and multi-stage latency/resource optimization across all six microservices of Project Aegis-Voice (`aegis-voice-core`) to guarantee law-enforcement grade reliability, SLA compliance, and zero-disk DPDP Act privacy invariants.

Working directory: k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core
Integrity mode: development

## Requirements

### R1. Comprehensive Multi-Service Automated Test Suite
Implement and execute automated unit, integration, and regression tests across the six microservices:
1. **Telephony Bridge:** FreeSWITCH dialplan media bug hooks (`SMBF_READ_STREAM`) and Asterisk AudioSocket frame parsing (20ms PCM chunks).
2. **Ingestion Gateway:** Silero VAD v5 ONNX filtering, SNR-routed split preprocessor (>25dB bypass, 10–25dB RNNoise for ASR), and ephemeral RAM-disk ring buffer (`shm_ring_buffer.py`).
3. **Acoustic SER Worker:** Continuous 3D $[V, A, D]$ regression, OpenSMILE eGeMAPS 88-dim CPU fallback, Frontier 2 zero-shot 3s prosodic baseline calibrator, and AASIST-L deepfake detector.
4. **Semantic ASR Worker:** IndicConformer CTC streaming transcription and in-stream deterministic PII regex FST scrubber (<1.8ms execution, zero raw Aadhaar/PAN/OTP leakage).
5. **Neuro-Symbolic Late Fusion:** Multimodal urgency formula $U(t)$, stoic victim shock paralysis detection, performative yelling cap, and I4C CFCFRMS JSON-LD lien generator.
6. **Dispatch UI & WebSockets:** WebSocket telemetry broadcast, dynamic queue re-ranking, and one-click lien push flow.

### R2. Deterministic Benchmark Evaluation & Adversarial Stress Validation
Build an evaluation benchmark suite simulating and scoring all core edge-case scenarios:
1. **Stoic Victim / Shock Paralysis:** Flat pitch variance ($\sigma_{F_0} < 8\text{ Hz}$, Arousal $< 0.35$) with high-value cybercrime intent automatically promoted to Priority-1 ($U \ge 0.85$).
2. **Performative Screaming / Yelling:** High loudness ($>80\text{ dB}$, Arousal $> 0.75$) with normal jitter ($<2.2\%$) and zero fraud intent strictly capped at Routine ($U \le 0.45$).
3. **Synthetic Deepfake Spoof:** AASIST-L phase entropy anomaly ($P_{\text{spoof}} > 0.70$) immediately suppressed to $U = 0.15$ with queue escalation blocked.
4. **Frontier 1 Scammer-in-the-Background Coercion:** Secondary laptop transducer roll-off ($<280\text{ Hz}$) combined with bimodal coaching turn-taking micro-pauses ($1.1\text{s} - 2.4\text{s}$).
5. **Silent Shadow Mode Statistical Gates:** Verification against 30-day baseline metrics (Golden-Hour fraud recall $\ge 94.0\%$, False Positive Rate $\le 8.5\%$, and Mean Early Lead-Time Advantage $\ge 110\text{s}$).

### R3. Pipeline Profiling, Concurrency Load Testing & Latency Optimization
1. Profile individual execution latencies across each stage (Ingestion $\le 25\text{ms}$, VAD $\le 2\text{ms}$, SER $\le 25\text{ms}$, ASR + PII $\le 125\text{ms}$, Late Fusion $\le 5\text{ms}$, UI Render $\le 18\text{ms}$).
2. Benchmark and optimize end-to-end glass-to-glass latency under simulated multi-call concurrency (target P50 $\le 450\text{ms}$, P99 $\le 600\text{ms}$, strictly within the $<800\text{ms}$ SLA).
3. Validate memory and storage invariants: verify zero `.wav` or `.pcm` disk persistence, confirming all raw audio resides exclusively in pinned RAM ring buffers.

## Acceptance Criteria

### Automated Testing & Coverage
- [ ] Automated regression suite covers all 6 microservices with 100% pass rate.
- [ ] Deterministic PII scrubber executes in $< 1.8\text{ms}$ with zero leakage of raw Aadhaar, PAN, OTP, or full bank account digits in test runs.

### Adversarial Evaluation
- [ ] Stoic shock victim scenario correctly activates Semantic Floor and receives Priority-1 badge ($U \ge 0.85$).
- [ ] Performative yelling scenario correctly capped at Routine priority ($U \le 0.45$).
- [ ] Synthetic voice deepfake scenario correctly blocked ($U = 0.15$).
- [ ] Frontier 1 secondary transducer coercion correctly flagged.
- [ ] Shadow mode evaluation passes all 3 statistical gates (Recall $\ge 94\%$, FPR $\le 8.5\%$, Lead Time $\ge 110\text{s}$).

### Performance & Latency SLA
- [ ] End-to-end glass-to-glass latency strictly verified $< 800\text{ms}$ SLA across all scenarios.
- [ ] Zero audio bytes written to SSD/NVMe disk confirmed during high-throughput execution.
- [ ] One-click reproducible CLI runner provided for continuous verification.

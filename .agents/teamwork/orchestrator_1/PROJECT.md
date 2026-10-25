# Project: Aegis-Voice Core Testing, Evaluation & Optimization

## Architecture
Six microservices forming sovereign emergency PSAP cybercrime interdiction pipeline:
1. `telephony-bridge`: FreeSWITCH dialplan media bug (`SMBF_READ_STREAM`) & Asterisk AudioSocket frame parser.
2. `ingestion-gateway`: Silero VAD v5 ONNX silence router, SNR split preprocessor (>25dB bypass, 10-25dB denoising), RAM ring buffer (`shm_ring_buffer.py`).
3. `acoustic-ser-worker`: Continuous 3D [V, A, D] regression, OpenSMILE eGeMAPS 88-dim CPU fallback, Frontier 2 zero-shot 3s prosodic baseline calibrator, AASIST-L deepfake detector.
4. `semantic-asr-worker`: IndicConformer CTC streaming transcription, in-stream deterministic PII regex FST scrubber (<1.8ms execution, zero raw Aadhaar/PAN/OTP leakage).
5. `neuro-symbolic-triage`: Multimodal urgency formula $U(t)$, stoic shock paralysis detection, performative yelling cap, I4C CFCFRMS JSON-LD lien generator, silent shadow evaluator.
6. `dispatch-ui`: WebSocket telemetry broadcast (`/ws/dispatch`), dynamic queue re-ranking, one-click lien push flow (`/api/authorize-lien`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | FreeSWITCH dialplan hooks | Dialplan XML & media bug frame handling (`SMBF_READ_STREAM`) | M2 | ORIGINAL_REQUEST §R1.1 |
| 2 | Asterisk AudioSocket gateway | Protocol header parsing (`!BH`) and 20ms PCM forwarding | M1, M2 | ORIGINAL_REQUEST §R1.1 |
| 3 | Silero VAD & SNR Router | Silence gating and SNR-routed split preprocessing (>25dB vs 10-25dB) | M1, M2 | ORIGINAL_REQUEST §R1.2 |
| 4 | Ephemeral RAM Ring Buffer | Zero-disk `collections.deque` ring buffer (`shm_ring_buffer.py`) | M2, M4 | ORIGINAL_REQUEST §R1.2, §R3.3 |
| 5 | Acoustic SER & 3D VAD Regression | Continuous [V, A, D] regression with OpenSMILE 88-dim fallback | M2 | ORIGINAL_REQUEST §R1.3 |
| 6 | SER Latency Optimization | FFT-based Wiener-Khinchin autocorrelation (<25ms SLA) | M1, M4 | ORIGINAL_REQUEST §R1.3, §R3.1 |
| 7 | Frontier 2 Prosodic Calibrator | Zero-shot 3s intra-caller baseline tracking ($\mu_{F_0}, \sigma_{F_0}, \Delta Z$) | M2, M3 | ORIGINAL_REQUEST §R1.3, §R2.5 |
| 8 | AASIST-L Deepfake Detector | Phase entropy and HF energy ratio spoof gating | M2, M3 | ORIGINAL_REQUEST §R1.3, §R2.3 |
| 9 | IndicConformer CTC Streaming | Streaming transcription worker with CTC decoding | M2 | ORIGINAL_REQUEST §R1.4 |
| 10 | PII Regex Scrubber | Deterministic in-stream scrubbing (<1.8ms execution) | M1, M2 | ORIGINAL_REQUEST §R1.4 |
| 11 | Spoken Digit PII Leak Fix | Collapse space-separated spoken digits to prevent Aadhaar/OTP/PAN leaks | M1, M2 | ORIGINAL_REQUEST §R1.4 |
| 12 | Multimodal Urgency Formula U(t) | Late fusion calculation with acoustic, semantic, and override terms | M2, M3 | ORIGINAL_REQUEST §R1.5, §R2 |
| 13 | Stoic Shock Paralysis Gate | Flat pitch ($\sigma_{F_0} < 8\text{ Hz}$), low arousal (<0.35) -> Priority-1 ($U \ge 0.85$) | M2, M3 | ORIGINAL_REQUEST §R1.5, §R2.1 |
| 14 | Performative Screaming Cap | High arousal (>0.75), low jitter (<2.2%), no fraud -> Routine ($U \le 0.45$) | M2, M3 | ORIGINAL_REQUEST §R1.5, §R2.2 |
| 15 | Synthetic Deepfake Suppression | Spoof probability > 0.70 clamped to $U = 0.15$ | M2, M3 | ORIGINAL_REQUEST §R1.5, §R2.3 |
| 16 | Frontier 1 Scammer Coercion | Roll-off <280Hz, micro-pauses 1.1s-2.4s detection | M2, M3 | ORIGINAL_REQUEST §R1.5, §R2.4 |
| 17 | I4C CFCFRMS JSON-LD Lien Builder | Schema-compliant lien payload staging and dispatch | M2 | ORIGINAL_REQUEST §R1.5 |
| 18 | Silent Shadow Mode Statistical Gates | Recall >= 94.0%, FPR <= 8.5%, Lead Time >= 110s validation | M2, M3 | ORIGINAL_REQUEST §R2.5 |
| 19 | WebSocket Telemetry Broadcast | Dynamic 60fps queue re-ranking and telemetry stream | M2 | ORIGINAL_REQUEST §R1.6 |
| 20 | One-Click Lien Push Flow | Transition call state from S4 to S5 on dispatcher authorization | M2 | ORIGINAL_REQUEST §R1.6 |
| 21 | Sub-Stage Latency Profiling | Ingestion <=25ms, VAD <=2ms, SER <=25ms, ASR+PII <=125ms, Fusion <=5ms, UI <=18ms | M4 | ORIGINAL_REQUEST §R3.1 |
| 22 | Glass-to-Glass Latency SLA | End-to-end P50 <=450ms, P99 <=600ms, max <800ms SLA | M4 | ORIGINAL_REQUEST §R3.2 |
| 23 | DPDP Zero-Disk Invariant | Zero .wav/.pcm disk writes, in-memory volatile execution | M4 | ORIGINAL_REQUEST §R3.3 |
| 24 | Continuous Verification CLI Runner | One-click CLI command executing full regression and validation | M4, M5 | ORIGINAL_REQUEST §R3.4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Pipeline Defect Fixes & Optimizations | SER FFT speedup, PII space-separated digit collapsing, VAD router wiring in /ws/stream, AudioSocket forwarding | none | DONE |
| M2 | Comprehensive Multi-Service Test Suite | Full automated test suite across all 6 microservices with pytest configuration and 100% pass rate | M1 | DONE |
| M3 | Deterministic Benchmark & Adversarial Validation | All 5 edge-case scenarios (Stoic, Screaming, Deepfake, Coercion, Shadow Gates) evaluated and verified | M1, M2 | DONE |
| M4 | Latency Profiling, Concurrency Load & Storage SLA | Profiling per-stage latencies, concurrency benchmark (P50/P99 <800ms), RAM zero-disk verification, CLI runner | M1, M2, M3 | DONE |
| M5 | Final Verification & Forensic Audit | End-to-end validation, Adversarial Challenger evaluation, Forensic Auditor integrity certification | M1, M2, M3, M4 | DONE |

## Interface Contracts
### Telephony Bridge ↔ Ingestion Gateway
- Protocol: WebSocket `ws://127.0.0.1:8080/ws/stream` or Asterisk AudioSocket TCP
- Format: 16kHz linear PCM, 16-bit mono signed integer chunks (20ms = 640 bytes or 320 samples)

### Ingestion Gateway ↔ SER / ASR
- Buffer: `EphemeralAudioRingBuffer` (window = 1.5s = 24,000 samples, `np.float32`)
- SER input: `audio_16k` numpy array shape `(24000,)`, output: `(valence, arousal, dominance, f0_hz, jitter_pct)`
- ASR input: `audio_16k` numpy array shape `(24000,)`, output: `{"transcript": str, "latency_ms": float}`

### ASR ↔ PII Scrubber
- Input: `raw_text` transcript string
- Output: `redacted_text` string, execution `< 1.8ms`, zero raw Aadhaar/PAN/OTP/Account digits

### SER + ASR ↔ Late Fusion
- Input: `(valence, arousal, dominance, sigma_f0_hz, f0_hz, jitter_pct, spoof_prob, s_semantic, override_active, threat_vectors)`
- Output: `{"urgency_score": float, "badge": str, "state": str, "p_freeze": float, "cfcfrms_payload": dict}`

### Late Fusion ↔ Dispatch UI
- WebSocket: `ws://127.0.0.1:8080/ws/dispatch`
- Payloads: `QUEUE_UPDATE`, `CALL_SELECT`, `LIEN_DISPATCHED`
- REST: `POST /api/authorize-lien`, `POST /api/officer-override`, `POST /api/stress-test`

## Code Layout
- `aegis-voice-core/telephony-bridge/`
  - `freeswitch_dialplan_1930.xml`
  - `mod_audio_stream_aegis.cpp`
  - `asterisk_audiosocket_gateway.py`
- `aegis-voice-core/ingestion-gateway/`
  - `ws_ingest_server.py`
  - `shm_ring_buffer.py`
  - `vad_denoiser_router.py`
- `aegis-voice-core/acoustic-ser-worker/`
  - `emotion2vec_trt_runner.py`
  - `opensmile_egemaps_fallback.py`
  - `frontier_coercion_calibration.py`
  - `aasist_spoof_guard.py`
- `aegis-voice-core/semantic-asr-worker/`
  - `indic_conformer_ctc.py`
  - `faster_whisper_stream.py`
  - `pii_redaction_fst.py`
- `aegis-voice-core/neuro-symbolic-triage/`
  - `late_fusion_engine.py`
  - `cfcfrms_jsonld_builder.py`
  - `shadow_evaluator.py`
- `aegis-voice-core/dispatch-ui/`
  - `public/index.html`
  - `src/` (LiveQueueBoard.tsx, WaveformArousalCanvas.tsx, XaiAttributionBadge.tsx)
- `aegis-voice-core/tests/` (New automated multi-service test suites)
- `aegis-voice-core/scripts/` (test_suite.py, run_verification.py, run_system.py)

# Dispatch for Test Writer M2

## Objective
Implement Milestone 2: Comprehensive Multi-Service Automated Test Suite across all 6 microservices of Project Aegis-Voice, ensuring 100% pass rate under `pytest`.

## Target Files to Create
- `aegis-voice-core/pytest.ini`
- `aegis-voice-core/tests/__init__.py`
- `aegis-voice-core/tests/test_telephony_bridge.py`
  - FreeSWITCH dialplan XML parsing & `SMBF_READ_STREAM` media bug hook verification.
  - Asterisk AudioSocket header parsing (`!BH`), length extraction, 20ms chunk framing (320 bytes 8kHz, 640 bytes 16kHz), 8k->16k upsampling, and WebSocket forwarding logic.
- `aegis-voice-core/tests/test_ingestion_gateway.py`
  - Silero VAD energy/ZCR silence vs speech discrimination.
  - SNR estimation and 3-way routing (>25dB bypass, 10-25dB spectral subtraction, <10dB raw).
  - `EphemeralAudioRingBuffer` zero-disk invariant, 75-frame (1.5s) deque capacity, window extraction, and memory deallocation.
  - Ingestion WebSocket endpoints (`/ws/stream`) with clean disconnects.
- `aegis-voice-core/tests/test_acoustic_ser.py`
  - Continuous 3D [V, A, D] regression and OpenSMILE eGeMAPS 88-dim CPU fallback.
  - FFT-based autocorrelation latency benchmark: assert execution time strictly <=25ms on 24,000 samples.
  - Frontier 2 zero-shot 3s prosodic baseline calibrator ($\mu_{F_0}, \sigma_{F_0}, \Delta Z$ tracking).
  - AASIST-L deepfake detector (phase entropy and HF energy ratio calculation).
- `aegis-voice-core/tests/test_semantic_asr.py`
  - IndicConformer CTC streaming transcription and FasterWhisper worker interfaces.
  - Deterministic PII regex FST scrubber latency benchmark: assert execution time strictly < 1.8ms.
  - Comprehensive PII masking tests across Hindi, English, and Hinglish spoken digit permutations:
    - Dictated Aadhaar ("nau aath chaar chaar ...") -> `XXXX-XXXX-8832` (zero raw Aadhaar digits leaked).
    - Dictated OTP ("chaar nau do ek ...") -> `[REDACTED-OTP]` (zero raw OTP digits leaked).
    - Dictated PAN card ("ABCDE1234F") -> `[REDACTED_PAN]`.
    - Dictated Bank Account -> `ACCT-XXXX-8832` (zero raw account digits leaked).
- `aegis-voice-core/tests/test_neuro_symbolic_fusion.py`
  - Multimodal urgency formula $U(t) = \min(1.0, 0.35 S_{\text{ac}} + 0.45 S_{\text{sem}} + 0.30 S_{\text{ac}}S_{\text{sem}} + 0.65 \mathbb{I}_{\text{override}})$.
  - Composite acoustic panic $\phi_{\text{vad}} = A(1-V)(1-D)$ and $S_{\text{ac}}$.
  - Stoic shock paralysis detection ($\sigma_{F_0} < 8\text{ Hz}$, $A < 0.35$ with cybercrime intent -> Priority-1 $U \ge 0.85$).
  - Performative yelling cap ($A > 0.75$, jitter $< 2.2\%$, zero fraud -> Routine $U \le 0.45$).
  - Synthetic deepfake suppression ($P_{\text{spoof}} > 0.70$ -> $U = 0.15$).
  - Frontier 1 scammer coercion detection (roll-off <280Hz, micro-pauses 1.1s-2.4s).
  - I4C CFCFRMS JSON-LD lien generator validation (@context, @type, statutory classification BNS 204/319, IT Act 66D, golden hour decay).
  - Silent shadow mode statistical gates (recall >= 94.0%, FPR <= 8.5%, lead time >= 110s).
- `aegis-voice-core/tests/test_dispatch_ui_websockets.py`
  - REST endpoints: `GET /api/health`, `GET /`, `POST /api/stress-test`, `POST /api/authorize-lien`, `POST /api/officer-override`.
  - WebSocket `/ws/dispatch`: initial queue broadcast, stream selection, dynamic queue re-ranking.
  - One-click lien push flow: transition state from S4 to S5 (`S5_LIEN_DISPATCHED_TO_NPCI`) and set `lien_pushed = True`.

## Execution & Acceptance
- Run `pytest aegis-voice-core/tests` and ensure 100% of tests pass.
- Write full report to `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\test_writer_m2\handoff.md`.


## 2026-10-25T06:38:49Z
Received dispatch from parent orchestrator 29f28c96-5ee8-41ee-b393-bf680b5f3bd1:
- Mission: Test Writer M2 for Project Aegis-Voice
- Implement pytest suite covering all 6 microservices
- Achieve 100% pass rate

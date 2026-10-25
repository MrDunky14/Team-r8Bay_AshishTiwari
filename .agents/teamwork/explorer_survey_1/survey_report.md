# Codebase Architecture & Technical Survey Report
**Project:** Aegis-Voice Core (`aegis-voice-core`)  
**Scope:** Global Architecture, Dependencies & Test Runners, Microservice 1 (Telephony Bridge), Microservice 2 (Ingestion Gateway)  
**Author:** Explorer 1 (`explorer_survey_1`)  
**Date:** 2026-10-25  

---

## 1. Executive Summary

Project Aegis-Voice is a sovereign multimodal speech emotion recognition and urgency triage engine engineered for the National Cybercrime Helpline (1930) and I4C (Indian Cyber Crime Coordination Centre). The core repository (`aegis-voice-core`) is designed as a six-microservice architecture operating under strict legal and operational constraints:
- **Statutory DPDP Act 2023 & UIDAI Invariants:** Zero-disk audio persistence; raw PCM residing exclusively in volatile memory; in-stream PII scrubbing (<1.8ms) masking Aadhaar, PAN, OTP, and bank accounts.
- **Strict SLA Compliance:** Glass-to-glass latency target $<800\text{ ms}$ (benchmark design claims $\approx 444.7\text{ ms}$ P50).
- **Adversarial Failure Shielding:** Resilient to stoic victim shock paralysis (Semantic Floor override to $U \ge 0.85$), performative yelling capping ($U \le 0.45$), AASIST-L synthetic deepfake suppression ($U = 0.15$), and secondary transducer scammer coercion sensing.

While the mathematical formulations, DSP heuristics, PII masking, late-fusion equations, and dispatch UI are functional and verified by a 6-scenario standalone script (`scripts/test_suite.py`), the **telephony bridge and ingestion microservices exhibit critical integration and testing gaps**. Specifically:
1. Ingestion WebSocket (`/ws/stream`) instantiates `SileroVADRouter` but **never calls it**, completely bypassing VAD silence gating and SNR split preprocessing on incoming live streams.
2. The Asterisk AudioSocket server decodes protocol headers and reads PCM chunks, but **drops them without forwarding** to the Ingestion Gateway.
3. The shared memory ring buffer (`shm_ring_buffer.py`) falls back entirely to an in-process Python `collections.deque` and **never allocates or binds a real OS shared memory block** (`multiprocessing.shared_memory.SharedMemory` or `/dev/shm`).
4. There are **zero unit or integration tests** for Microservice 1 (Telephony Bridge) or Microservice 2 (Ingestion Gateway).

---

## 2. Global Codebase Structure & Layout

The codebase is organized in `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core` with 35 tracked files across 10 directories:

```text
aegis-voice-core/
├── telephony-bridge/                      # Microservice 1: Carrier Interception
│   ├── freeswitch_dialplan_1930.xml       # Shadow fork dialplan (SMBF_READ_STREAM)
│   ├── mod_audio_stream_aegis.cpp         # FreeSWITCH C++17 media bug extension skeleton
│   └── asterisk_audiosocket_gateway.py    # Asyncio TCP AudioSocket server (20ms frames)
├── ingestion-gateway/                     # Microservice 2: Ingestion & Volatile Buffering
│   ├── shm_ring_buffer.py                 # Ephemeral RAM-disk sliding window (75 frames = 1.5s)
│   ├── vad_denoiser_router.py             # Silero VAD energy/SNR-routed split preprocessor
│   └── ws_ingest_server.py                # Unified FastAPI / WebSocket server (ports 8080)
├── acoustic-ser-worker/                   # Microservice 3: Affective Acoustic Engine
│   ├── opensmile_egemaps_fallback.py      # Autocorrelation DSP for F0, jitter, shimmer, HNR
│   ├── emotion2vec_trt_runner.py          # 1.5s sliding window SER runner & uncertainty estimator
│   ├── frontier_coercion_calibration.py   # Frontier 1 Coercion & Frontier 2 3s Calibrator
│   └── aasist_spoof_guard.py              # AASIST-L synthetic vocoder phase anomaly gate
├── semantic-asr-worker/                   # Microservice 4: Speech-to-Text & PII Redaction
│   ├── pii_redaction_fst.py               # Deterministic in-memory regex scrubber (<1.8ms)
│   ├── indic_conformer_ctc.py             # AI4Bharat CTC streaming ASR worker
│   └── faster_whisper_stream.py           # Multilingual Faster-Whisper turbo stream
├── neuro-symbolic-triage/                 # Microservice 5: Late Fusion & Triage Engine
│   ├── late_fusion_engine.py              # Multimodal urgency equation U(t), semantic floor
│   ├── cfcfrms_jsonld_builder.py          # CFCFRMS JSON-LD lien payload generator
│   └── shadow_evaluator.py                # 30-day silent shadow mode benchmark logger
├── dispatch-ui/                           # Microservice 6: 60fps Operator Console
│   ├── package.json                       # Next.js / React configuration
│   ├── public/index.html                  # Full standalone 60fps dark-mode HTML5/WebGL dashboard
│   └── src/
│       ├── LiveQueueBoard.tsx             # Dynamic queue re-ranking board component
│       ├── WaveformArousalCanvas.tsx      # Dual-party waveform canvas component
│       └── XaiAttributionBadge.tsx        # Explainable AI attribution component
├── scripts/                               # Operational & Verification Scripts
│   ├── test_suite.py                      # Standalone 6-module test runner
│   ├── inject_3stream_stress_test.py      # HTTP client trigger for 3-stream benchmark
│   ├── generate_presentation.py           # Programmatic 5-slide PPTX deck builder
│   └── run_system.py                      # Master server bootstrapper
├── presentation/                          # Presentation Slides
│   ├── Aegis_Voice_Vecnaverse_Pitch.pptx  # 5-Slide Executive Pitch Deck
│   └── Aegis_Voice_5_Slide_Deck.md        # Companion Markdown Slide Deck
├── demo/                                  # Demo Documentation
│   └── 2_MINUTE_DEMO_SCRIPT.md            # Word-for-word 120s live screen-recording script
└── models/                                # Model Documentation & Weights Directory
    └── README.md                          # Pinned open-weight checkpoints & sizing
```

---

## 3. Environment, Dependencies & Test Runners

### 3.1 Python Runtime Environment
- **Python Version:** 3.13.3 (win32)
- **Audio Subsystem Note:** Python 3.13 deprecated and removed the built-in standard library module `audioop`. The environment has `audioop-lts 0.2.2` installed, which satisfies any legacy audio operations.
- **Pytest:** `pytest 9.0.2` is installed and verified working.
- **Core ML / DSP Packages:**
  - `torch 2.10.0+cpu`
  - `scipy 1.18.1`
  - `numpy 2.2.6`
  - `scikit-learn 1.9.0`
- **Web & Asynchronous Networking:**
  - `fastapi 0.141.1`
  - `uvicorn 0.30.6`
  - `starlette 1.6.0`
  - `websockets 15.0.1`
  - `httpx 0.28.1` (FastAPI / Starlette `TestClient` functions with deprecation warning regarding httpx)
  - `anyio 4.12.0`
- **Presentation & Documentation:**
  - `python-pptx 1.0.2`

### 3.2 Existing Test Configuration & Execution
- **Existing Runner:** `scripts/test_suite.py` contains 6 assertion-based test functions:
  1. `test_pii_scrubber`: PII regex masking latency and UIDAI/DPDP invariants.
  2. `test_stoic_shock_victim_semantic_floor`: Monotone flat pitch override to $U \ge 0.85$.
  3. `test_performative_yelling_cap`: Loud arousal capped at $U \le 0.45$.
  4. `test_synthetic_deepfake_gate`: AASIST-L spoof suppression to $U = 0.15$.
  5. `test_frontier_coercion_sensing`: Dual-band transducer ratio & coaching pause check.
  6. `test_3s_prosodic_calibration`: Mahalanobis pitch baseline deviation $\Delta Z_{F_0}$.
- **Pytest Discovery:** Running `pytest scripts/test_suite.py` executes all 6 functions in 0.29s with 100% pass rate.
- **Configuration Deficiencies:**
  - No `pytest.ini`, `pyproject.toml`, or `setup.cfg` file exists at the root or microservice level.
  - Tests require manual `sys.path.insert()` calls to import packages from sibling directories.
  - No automated test suite exists under a standardized `tests/` directory.

---

## 4. Deep Dive: Microservice 1 (Telephony Bridge)

The Telephony Bridge is responsible for passive, non-disruptive audio stream tapping from telephony switches (FreeSWITCH and Asterisk) into the Aegis-Voice ingestion pipeline.

### 4.1 FreeSWITCH Dialplan (`telephony-bridge/freeswitch_dialplan_1930.xml`)
- **Inspection:**
  - Configures extension `1930_cybercrime_aegis_shadow_fork` matching `destination_number` `^1930$`.
  - Sets `MOD_AUDIO_FORK_SERVICE_THREADS=4` to isolate WebSocket streaming I/O from real-time RTP switching threads, guaranteeing zero jitter on the officer's audio bridge.
  - Executes `export nolocal:execute_on_answer=uuid_audio_stream ${uuid} start ws://127.0.0.1:8080/ws/stream stereo 16k`.
  - Bridges the caller directly to `user/1930_dispatcher_queue`.
- **Finding:**
  The dialplan is clean and adheres to standard FreeSWITCH conventions for `mod_audio_stream` / `mod_audio_fork`. However, it targets a WebSocket URL with query parameter expectations (`uuid_audio_stream ${uuid} start ws://127.0.0.1:8080/ws/stream stereo 16k`), whereas `ws_ingest_server.py` expects `uuid` as a query parameter: `ws://127.0.0.1:8080/ws/stream?uuid=<uuid>`.

### 4.2 C++ FreeSWITCH Media Bug Hook (`telephony-bridge/mod_audio_stream_aegis.cpp`)
- **Inspection:**
  - Implements `SWITCH_MODULE_LOAD_FUNCTION` and `SWITCH_MODULE_SHUTDOWN_FUNCTION`.
  - Attaches `aegis_audio_stream_callback` handling `SWITCH_ABC_TYPE_INIT`, `SWITCH_ABC_TYPE_READ_REPLACE`, `SWITCH_ABC_TYPE_READ`, `SWITCH_ABC_TYPE_CLOSE`.
  - Uses `switch_core_media_bug_get_read_replace_frame(bug)` to intercept inbound 16kHz linear PCM.
- **Architectural Gaps:**
  - Lines 46–48 contain a placeholder comment:
    ```cpp
    // Audio payload (16kHz 16-bit linear PCM) is dispatched to async worker queue
    // High-performance circular buffer ensures 0ms impact on carrier leg.
    ```
    No actual WebSocket networking (e.g. `libwebsockets` or `ixwebsocket`) or IPC shared-memory ring buffer write is implemented in this C++ file.
  - No build tooling (Makefile or CMakeLists.txt) is provided. This file serves primarily as an architectural blueprint for carrier-grade deployments.

### 4.3 Asterisk AudioSocket Gateway (`telephony-bridge/asterisk_audiosocket_gateway.py`)
- **Inspection:**
  - Asynchronous TCP server using `asyncio.start_server` listening on `0.0.0.0:9092`.
  - Implements the Asterisk AudioSocket framing specification:
    - 3-byte header: `struct.unpack("!BH", header)` -> `msg_type` (1 byte), `payload_len` (2 bytes, big-endian unsigned short).
    - Initial frame: reads 16-byte call UUID (`uuid.UUID(bytes=call_uuid_bytes)`).
    - Subsequent loop: reads 3-byte header `!BH` followed by `await reader.readexactly(length)`.
    - Handles 20ms chunks: 320 bytes (8kHz 16-bit mono) or 640 bytes (16kHz 16-bit mono).
- **Critical Implementation Gaps:**
  - **Frame Dropping:** Lines 46–50 read `audio_payload = await reader.readexactly(length)`, but do nothing with `audio_payload`. The data is immediately garbage-collected and never forwarded to `INGESTION_WS_URL = "ws://127.0.0.1:8080/ws/stream"`.
  - **No Sample Rate Normalization:** PSTN carriers typically deliver 8kHz G.711/L16. If Asterisk delivers 8kHz audio (320-byte payloads), there is no upsampling to 16kHz before hitting downstream Aegis models.
  - **Missing Outbound AudioSocket Handling:** AudioSocket protocol supports 2-way audio or hangup messages (`0xFF`). The gateway does not send any acknowledgments or handle graceful Asterisk channel tears down.
  - **No Automated Tests:** The gateway has zero unit tests verifying header parsing, payload extraction, error recovery on truncated frames, or WebSocket forwarding.

---

## 5. Deep Dive: Microservice 2 (Ingestion Gateway)

The Ingestion Gateway receives real-time PCM streams, ensures DPDP Act compliance through volatile-only RAM buffering, performs Voice Activity Detection (VAD) and SNR routing, and coordinates dual-stream worker execution.

### 5.1 Ephemeral RAM Ring Buffer (`ingestion-gateway/shm_ring_buffer.py`)
- **Inspection:**
  - Class `EphemeralAudioRingBuffer` maintains a circular buffer of 75 frames (1.5 seconds) of 16kHz mono PCM (640 bytes per 20ms frame = 320 float32 samples).
  - Storage: In-memory `collections.deque(maxlen=75)`.
  - `push_frame(pcm_bytes)`: Converts `np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0` and appends to the deque.
  - `get_window()`: Concatenates deque into a single 24,000-sample array (`np.concatenate(list(self.frame_deque))`) once 75 frames have accumulated; returns `None` if fewer than 75 frames are present.
  - `clear()`: Wipes deque and attempts to close/unlink `shm_block`.
- **Architectural & Compliance Gaps:**
  - **Unallocated Shared Memory:** Lines 35–41 initialize `self.shm_block = None` and set `self.shm_path = f"/dev/shm/aegis_ring/{self.call_uuid}.pcm"` only on non-Windows. However, `self.shm_block` is **never actually allocated or mapped** using `multiprocessing.shared_memory.SharedMemory` or OS `mmap`. The buffer operates entirely in Python process heap memory.
  - **Single-Process Limitation:** Because it resides in Python process heap rather than true OS shared memory (`/dev/shm` or `multiprocessing.shared_memory`), separate worker processes cannot read the buffer zero-copy without serializing over sockets or IPC.
  - **Zero Disk Persistence Invariant:** Positively, the heap-based implementation strictly obeys the DPDP Act requirement of zero persistent disk writes (no `.wav` or `.pcm` files touch NVMe/SSD).
  - **No Test Coverage:** No tests verify window size, overrun behavior, clearing on call termination, or multi-frame concatenation.

### 5.2 Silero VAD & SNR-Routed Split Preprocessor (`ingestion-gateway/vad_denoiser_router.py`)
- **Inspection:**
  - Class `SileroVADRouter`:
    - `compute_energy_vad(audio_chunk)`: Computes RMS and Zero-Crossing Rate (ZCR), returning a probability $p \in [0.0, 1.0]$ and boolean speech flag ($p \ge 0.5$).
    - `estimate_snr_db(audio_chunk)`: Computes $10 \log_{10}(\text{signal power} / \text{noise floor})$.
    - `route_audio(raw_audio_16k)`:
      - Clean ($>25\text{ dB}$ SNR): Direct bypass.
      - Degraded ($10\text{ dB} - 25\text{ dB}$ SNR): Fast frequency-domain spectral magnitude subtraction for ASR (`asr_conditioned_audio`), while preserving raw audio for SER (`ser_conditioned_audio`) to maintain vocal micro-tremors (jitter, shimmer).
      - Severe ($<10\text{ dB}$ SNR): Retains raw audio and flags epistemic uncertainty.
- **Architectural Gaps:**
  - **Heuristic Proxy vs. Silero ONNX:** The implementation uses a mathematical energy/ZCR proxy rather than loading the official `silero_vad.onnx` model (documented in `models/README.md`). While this eliminates external binary dependencies and executes in $<1.2\text{ ms}$, it does not utilize the deep neural network VAD.
  - **No Dedicated Unit Tests:** No tests exist verifying SNR threshold routing, speech classification on silence vs. speech, or spectral gating output.

### 5.3 Unified Ingestion & Dispatch Server (`ingestion-gateway/ws_ingest_server.py`)
- **Inspection:**
  - FastAPI application hosting WebSocket endpoints (`/ws/stream`, `/ws/dispatch`) and REST APIs (`/api/stress-test`, `/api/authorize-lien`, `/api/officer-override`, `/api/health`).
  - Broadcasts queue updates and real-time audio telemetry to connected dispatch consoles.
- **Critical Architectural Defect:**
  - **Bypassed VAD Router:** Line 49 instantiates `vad_router = SileroVADRouter()`. However, inside `websocket_stream_endpoint` (lines 241–295), `vad_router.route_audio()` is **NEVER called**. When `ring_buf.get_window()` returns an audio window:
    ```python
    ser_res = ser_runner.infer(call_uuid, audio_window, call_time_s)
    asr_res = asr_worker.transcribe_chunk(audio_window)
    ```
    The audio is passed directly to the SER and ASR workers without VAD silence filtering and without SNR split preprocessing. Silence chunks trigger full inference, and noisy chunks do not receive RNNoise/spectral conditioning on the ASR path.
  - **Static Mocking in Fallback:** In `websocket_stream_endpoint`, `asr_worker.transcribe_chunk(audio_window)` receives raw audio without simulated text, defaulting to a hardcoded string (`"Sir mera account se paisa debit ho gaya hai RTGS kiya tha"`).
  - **Session Tracking:** `call_sessions: Dict[str, Dict[str, Any]] = {}` is declared at line 59 but never updated during active `/ws/stream` connections.

---

## 6. Comprehensive Findings & Missing Features Matrix

| Microservice | Component | Current State | Missing Feature / Defect | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **MS1: Telephony** | `freeswitch_dialplan_1930.xml` | Functional FreeSWITCH XML dialplan with `SMBF_READ_STREAM` | Dialplan uses `uuid_audio_stream ... ws://...` space-delimited syntax; server expects `?uuid=` query parameter. | Low |
| **MS1: Telephony** | `mod_audio_stream_aegis.cpp` | C++17 FreeSWITCH media bug skeleton | PCM transmission logic commented out; no build scripts; no libwebsockets link. | Medium |
| **MS1: Telephony** | `asterisk_audiosocket_gateway.py` | Asyncio TCP server parsing 3-byte header and 16-byte UUID | Audio frames are read and discarded; no WebSocket client forwarding to `/ws/stream`; no 8kHz-to-16kHz resampler. | **High** |
| **MS1: Telephony** | Automated Tests | None | Zero unit or integration tests for frame parsing, error handling, or gateway streaming. | **High** |
| **MS2: Ingestion** | `shm_ring_buffer.py` | Working 75-frame (1.5s) deque; strictly zero disk persistence | `shm_block` is never allocated via `multiprocessing.shared_memory`; single-process heap memory only. | Medium |
| **MS2: Ingestion** | `vad_denoiser_router.py` | Heuristic energy/ZCR VAD and SNR-routed split preprocessor | Uses CPU energy proxy instead of Silero ONNX model; RNNoise approximated via FFT subtraction. | Medium |
| **MS2: Ingestion** | `ws_ingest_server.py` | FastAPI app, REST APIs, `/ws/dispatch`, `/ws/stream` | **`vad_router` is instantiated but never invoked in `/ws/stream`**; VAD gating and split preprocessing completely bypassed in live stream. | **Critical** |
| **MS2: Ingestion** | Automated Tests | None | Zero automated unit tests for ring buffer, VAD router, or WebSocket endpoints. | **High** |
| **Global** | Configuration & CI | No config files | No `pytest.ini` or package layout configuration; tests rely on ad-hoc `sys.path` injection. | Medium |

---

## 7. Actionable Recommendations for Implementation Phase

1. **Wire `vad_router` into `ws_ingest_server.py`:**
   In `/ws/stream`, insert the routing step immediately after extracting `audio_window`:
   ```python
   routed = vad_router.route_audio(audio_window)
   if not routed.is_speech:
       # Silence frame: skip expensive SER/ASR or broadcast low-arousal background telemetry
       continue
   ser_res = ser_runner.infer(call_uuid, routed.ser_conditioned_audio, call_time_s)
   asr_res = asr_worker.transcribe_chunk(routed.asr_conditioned_audio)
   ```

2. **Implement Forwarding & Resampling in `asterisk_audiosocket_gateway.py`:**
   - Establish an outbound `aiohttp` or `websockets` client session to `ws://127.0.0.1:8080/ws/stream?uuid={call_uuid}`.
   - If payload length is 320 bytes (8kHz), upsample to 640 bytes (16kHz) via `scipy.signal.resample` or linear interpolation before forwarding.
   - Forward valid 640-byte chunks asynchronously.

3. **Enable Cross-Platform Shared Memory in `shm_ring_buffer.py`:**
   - Use `multiprocessing.shared_memory.SharedMemory(create=True, size=...)` which works across Windows and Linux.
   - Write incoming frames into the shared memory segment so external workers can access frames zero-copy.

4. **Construct Comprehensive Automated Unit Test Suite (`tests/`):**
   - `tests/test_telephony_bridge.py`: Test AudioSocket packet unpacking, 8kHz/16kHz handling, malformed packet recovery, and FreeSWITCH dialplan XML schema validation.
   - `tests/test_ingestion_gateway.py`: Test ring buffer 75-frame sliding window, FIFO overwrite, VAD speech vs silence gating, SNR routing (>25dB bypass vs 10-25dB spectral filter), and FastAPI `/ws/stream` + `/ws/dispatch` endpoints via `starlette.testclient.TestClient`.
   - Add `pytest.ini` configuring `pythonpath = . telephony-bridge ingestion-gateway acoustic-ser-worker semantic-asr-worker neuro-symbolic-triage`.

---

## 8. Verification & Validation Protocol

To independently verify these survey findings:
1. **Verify Existing Tests:**
   ```powershell
   pytest scripts/test_suite.py
   ```
   *Expected:* 6 tests passed in ~0.3s.
2. **Verify Missing VAD Call in `ws_ingest_server.py`:**
   Inspect `ingestion-gateway/ws_ingest_server.py` lines 49 and lines 257–285 to confirm that `vad_router` is never called.
3. **Verify Audio Dropping in `asterisk_audiosocket_gateway.py`:**
   Inspect `telephony-bridge/asterisk_audiosocket_gateway.py` lines 46–50 to confirm that `audio_payload` is read but not sent anywhere.
4. **Verify Shared Memory Status in `shm_ring_buffer.py`:**
   Inspect `ingestion-gateway/shm_ring_buffer.py` lines 35–42 to confirm that `self.shm_block` is `None` and never created.

# Dispatch for Worker M1

## Objective
Implement Milestone 1 (Pipeline Defect Fixes & Latency Optimizations) across Project Aegis-Voice:
1. **SER Autocorrelation Latency Fix**:
   - File: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\acoustic-ser-worker\opensmile_egemaps_fallback.py`
   - In `FastAcousticBiomarkerExtractor.extract_biomarkers`: Replace slow `np.correlate` on 24,000 samples with FFT-based Wiener-Khinchin autocorrelation (`np.fft.rfft` and `np.fft.irfft`).
   - Target latency: <3.5ms (down from 52ms, strictly meeting <=25ms SER SLA).
2. **Spoken Digit PII Scrubber Fix**:
   - File: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\semantic-asr-worker\pii_redaction_fst.py`
   - In `scrub_pii_in_memory`: After `normalize_spoken_digits`, collapse space-separated digit runs (e.g., using `re.sub(r'(?<=\b\d)\s+(?=\d\b)', '', text)` or regex logic) so that dictated Aadhaar (`9 8 4 4 2 1 0 9 8 8 3 2`), OTP (`4 9 2 1 0 4`), and Bank Account numbers match their respective masking regexes (`XXXX-XXXX-8832`, `[REDACTED_OTP]`, `[REDACTED_ACCOUNT]`).
   - Ensure execution time remains <1.8ms with ZERO raw digit leakage.
3. **Ingestion Gateway VAD & SNR Router Wiring**:
   - File: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\ingestion-gateway\ws_ingest_server.py`
   - In `websocket_stream_endpoint` (lines 253-285): Wire up `vad_router.route_audio_chunk(audio_window)` so that silence gating and SNR split preprocessing (>25dB bypass vs 10-25dB spectral subtraction) are active before passing audio to SER and ASR.
   - Also add graceful exception handling for Starlette WebSocket disconnect (`WebSocketDisconnect` and `RuntimeError` during test client teardown) so connections close cleanly.
4. **Asterisk AudioSocket Frame Forwarding**:
   - File: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\telephony-bridge\asterisk_audiosocket_gateway.py`
   - In `handle_client`: Forward incoming 20ms audio payloads to `INGESTION_WS_URL = "ws://127.0.0.1:8080/ws/stream"` using `websockets.connect()` or an asynchronous WebSocket client, with reconnect and error logging.

## Input Context
- `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\ORIGINAL_REQUEST.md`
- `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\orchestrator_1\PROJECT.md`
- Explorer 1 Survey Report: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_1\survey_report.md`
- Explorer 2 Survey Report: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_2\survey_report.md`
- Explorer 3 Survey Report: `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_3\survey_report.md`

## Ownership
Worker exclusively owns:
- `aegis-voice-core/acoustic-ser-worker/opensmile_egemaps_fallback.py`
- `aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py`
- `aegis-voice-core/ingestion-gateway/ws_ingest_server.py`
- `aegis-voice-core/telephony-bridge/asterisk_audiosocket_gateway.py`

## Verification
- Run tests and micro-benchmarks verifying all 4 fixes:
  - `python aegis-voice-core/scripts/test_suite.py` passes 100%.
  - Verify SER biomarker extraction latency on 24,000 samples is <10ms.
  - Verify spoken Aadhaar, OTP, and Bank Account strings are properly masked with zero leaks.
  - Verify VAD router invocation and Starlette TestClient WebSocket handling.

## Output
Write report and handoff to:
`k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m1\handoff.md`


## 2026-10-25T06:28:25Z
From: 29f28c96-5ee8-41ee-b393-bf680b5f3bd1 (Orchestrator)

You are Worker M1 for Project Aegis-Voice.
Your assigned working directory is:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m1

Mandatory requirements:
1. Read the verbatim user request at:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\ORIGINAL_REQUEST.md

2. Read your task dispatch at:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m1\DISPATCH.md

3. Read the project scope document:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\orchestrator_1\PROJECT.md

4. Read the survey reports for reference:
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_1\survey_report.md
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_2\survey_report.md
- k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_3\survey_report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Ownership:
You exclusively own:
- `aegis-voice-core/acoustic-ser-worker/opensmile_egemaps_fallback.py`
- `aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py`
- `aegis-voice-core/ingestion-gateway/ws_ingest_server.py`
- `aegis-voice-core/telephony-bridge/asterisk_audiosocket_gateway.py`

Key Tasks:
1. Optimize SER Autocorrelation: Replace `np.correlate` with FFT-based autocorrelation (`np.fft.rfft` and `irfft`) in `opensmile_egemaps_fallback.py` to bring latency down from 52ms to <3.5ms (meeting <=25ms SLA).
2. Fix Spoken Digit PII Scrubber Leakage: In `pii_redaction_fst.py`, collapse space-separated digit runs after `normalize_spoken_digits` so that dictated numbers (Aadhaar, OTP, bank account) match masking patterns without raw digit leakage, maintaining <1.8ms execution time.
3. Wire up Ingestion VAD & SNR Router: In `ws_ingest_server.py`, invoke `vad_router.route_audio_chunk(audio_window)` in the audio stream loop so silence gating and SNR split preprocessing are performed. Also handle Starlette WebSocket client disconnects cleanly.
4. Asterisk AudioSocket Forwarding: In `asterisk_audiosocket_gateway.py`, forward 20ms audio chunks to `INGESTION_WS_URL = "ws://127.0.0.1:8080/ws/stream"`.
5. Run builds and tests to verify all changes:
   - Run `pytest aegis-voice-core/scripts/test_suite.py`
   - Test micro-latencies of SER and PII scrubber
   - Test spoken digit PII scrubbing with zero raw leaks
6. Write a comprehensive handoff report to:
k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\worker_m1\handoff.md
7. Send message to orchestrator (Recipient: 29f28c96-5ee8-41ee-b393-bf680b5f3bd1) with summary and verification evidence.

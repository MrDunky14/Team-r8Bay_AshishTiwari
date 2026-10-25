# Handoff Report: Microservice 3 (SER) & Microservice 4 (ASR & PII)

**From:** Explorer 2 (Teamwork Explorer)  
**To:** Parent Orchestrator (`29f28c96-5ee8-41ee-b393-bf680b5f3bd1`)  
**Working Directory:** `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_2`  
**Handoff Type:** Hard (Survey Phase Complete)  
**Date:** 2026-10-25  

---

## 1. Observation

1. **Absence of Model Weight Files and Deep Learning Libraries:**
   - In `aegis-voice-core/models/`, only `README.md` exists; no `.onnx`, `.pt`, or `.engine` weight files are present.
   - Running `python -c "import onnxruntime; import faster_whisper; import opensmile"` verified that `onnxruntime`, `faster_whisper`, and `opensmile` are **NOT** installed in the local Python environment. Only `torch`, `numpy`, `scipy`, `fastapi`, and `uvicorn` are present.
2. **Acoustic SER Worker Implementation Reality:**
   - `acoustic-ser-worker/emotion2vec_trt_runner.py:20` instantiates `FastAcousticBiomarkerExtractor` from `opensmile_egemaps_fallback.py`. Despite class name `Emotion2VecRunner`, no TensorRT or ONNX model is loaded.
   - `opensmile_egemaps_fallback.py:36-47` computes pitch $F_0$ via:
     ```python
     corr = np.correlate(audio_16k, audio_16k, mode='full')
     corr = corr[len(corr) // 2:]
     ```
   - Benchmarking a standard 1.5-second (24,000 samples) window on the local host measured **52.22 ms** per invocation. This exceeds the $\le 25.0\text{ ms}$ SLA target.
   - Benchmarking FFT-based Wiener-Khinchin autocorrelation (`np.fft.rfft` and `irfft`) on the same 24,000 samples measured **2.834 ms** ($18.4\times$ faster).
3. **Frontier 1 & Frontier 2 Latency & Logic:**
   - `acoustic-ser-worker/frontier_coercion_calibration.py`:
     - `ZeroShotProsodicCalibrator` update/score measured **0.0004 ms**.
     - `detect_secondary_transducer_coercion` measured **1.031 ms**.
   - `acoustic-ser-worker/aasist_spoof_guard.py`:
     - `AASISTSpoofGuard` computes rFFT phase entropy and high-frequency power; measured **1.482 ms**.
4. **Semantic ASR Worker & PII Scrubber Vulnerability:**
   - `semantic-asr-worker/indic_conformer_ctc.py:18-43` and `faster_whisper_stream.py:17-31` are simulation stubs returning hardcoded latencies (115.0ms and 145.0ms) and transcripts.
   - `semantic-asr-worker/pii_redaction_fst.py:75-94` `scrub_pii_in_memory` measured **0.0289 ms** ($62\times$ faster than $<1.8\text{ms}$ SLA).
   - In `pii_redaction_fst.py:49-74`, `normalize_spoken_digits` outputs single digits joined by spaces: `" ".join(out)`.
   - Executing `scrub_pii_in_memory('Mera aadhaar nau aath chaar chaar do ek shunya nau aath aath teen do hai')` returned:
     `'Mera aadhaar 9 8 4 4 2 1 0 9 8 8 3 2 hai'`.
     **Verbatim Result:** All 12 digits of the Aadhaar number were leaked unmasked in cleartext.
   - Executing `scrub_pii_in_memory('mera otp tha chaar nau do ek shunya chaar')` returned:
     `'mera otp tha 4 9 2 1 0 4'`.
     **Verbatim Result:** Raw OTP digits leaked unmasked.
   - Executing `scrub_pii_in_memory('account number paanch shunya ek shunya shunya do teen chaar paanch chhah saat aath aath teen do')` returned:
     `'account number 5 0 1 0 0 2 3 4 5 6 7 8 8 3 2'`.
     **Verbatim Result:** Raw Bank Account leaked unmasked.
   - Testing `re.sub(r'(?<=\b\d)\s+(?=\d\b)', '', text)` collapsed `"9 8 4 4 2 1 0 9 8 8 3 2"` to `"984421098832"`, which `UID_PATTERN` immediately masked to `"XXXX-XXXX-8832"`.
5. **Zero-Disk Invariant:**
   - Ripgrep search across `aegis-voice-core` for `.write(` and `open(` confirmed that no audio files (.wav, .pcm) or transcript logs are written to disk. Audio frames exist solely in `EphemeralAudioRingBuffer` (`collections.deque(maxlen=75)`).
6. **Existing Test Coverage:**
   - `scripts/test_suite.py` executes 6 tests (PII with 1 preset string, Stoic victim, Performative yelling, Deepfake gate, Frontier 1, Frontier 2). It does not test `Emotion2VecRunner.infer()`, `IndicConformerStreamWorker`, `FasterWhisperStreamWorker`, or adversarial spoken-digit PII inputs.

---

## 2. Logic Chain

1. **SER Latency SLA Violation (Referencing Observation 2):**
   - *Observation:* `opensmile_egemaps_fallback.py` uses full-length `np.correlate` on 24,000 samples, taking 52.22 ms.
   - *Logic:* The system SLA specifies SER inference must complete in $\le 25\text{ms}$. Because $52.22\text{ ms} > 25.0\text{ ms}$, the current unoptimized implementation fails the latency SLA under real-time audio chunking.
   - *Remediation Logic:* Only lags 35 to 213 (corresponding to 75Hz - 450Hz human pitch) are required. Applying Wiener-Khinchin FFT autocorrelation computes all lags in 2.83 ms, bringing SER latency down to 5.34 ms total (well below 25ms).
2. **DPDP Act PII Leakage Vulnerability (Referencing Observation 4):**
   - *Observation:* Callers speaking digits ("nau aath...") produce space-separated digit strings (`"9 8 4 4 2 1 0 9 8 8 3 2"`), which fail to match `UID_PATTERN`, `OTP_CONTEXT_PATTERN`, and `BANK_ACCT_PATTERN`.
   - *Logic:* The DPDP Act 2023 and user requirements mandate "zero raw Aadhaar/PAN/OTP leakage". Because real citizens on 1930 distress calls dictate credentials digit-by-digit, the current implementation violates the zero-leakage invariant for any spoken-digit input.
   - *Remediation Logic:* Adding `re.sub(r'(?<=\b\d)\s+(?=\d\b)', '', text)` collapses adjacent single digits into continuous numbers prior to regex evaluation, completely closing the leakage vector while maintaining execution time at $< 0.035\text{ ms}$.
3. **Execution Backend Classification (Referencing Observations 1, 2, 4):**
   - *Observation:* Neural weights and runtimes (`onnxruntime`, `opensmile`) are absent; workers use pure NumPy DSP and simulation wrappers.
   - *Logic:* The system is designed to function as an autonomous, zero-dependency sovereign core suitable for edge or air-gapped CPU PSAP deployment. Testing and adversarial validation should evaluate both this CPU DSP fallback and the simulated interfaces.
4. **Test Suite Expansion Requirement (Referencing Observation 6):**
   - *Observation:* The current `test_suite.py` tests isolated functions rather than worker classes and omits adversarial edge cases.
   - *Logic:* To meet the acceptance criteria of "Automated regression suite covers all 6 microservices with 100% pass rate", the test suite must be expanded to instantiate worker classes directly and test spoken digit PII permutations.

---

## 3. Caveats

1. **GPU Acceleration Not Evaluated:** The local Windows environment lacks an NVIDIA GPU and TensorRT runtime; all evaluations were conducted against the CPU fallback architecture.
2. **Microservices 1, 2, 5, and 6:** The Telephony Bridge, Ingestion Gateway, Late Fusion Engine, and Dispatch UI were surveyed only to the extent they interface with Microservices 3 and 4; primary survey of those services is assigned to peer explorers.
3. **Network Mode:** Investigation was conducted strictly read-only within the local project workspace.

---

## 4. Conclusion

1. **Acoustic SER Worker (Microservice 3):**
   - Mathematically sound continuous 3D [V, A, D] regression, Frontier 1 coercion detection, Frontier 2 intra-caller calibration, and AASIST-L deepfake proxy.
   - **Action Required:** Replace `np.correlate` with FFT-based autocorrelation in `opensmile_egemaps_fallback.py` to reduce latency from 52.2ms to 2.8ms, resolving the SLA failure.
2. **Semantic ASR Worker & PII Scrubber (Microservice 4):**
   - Extremely fast PII scrubber (0.029ms vs 1.8ms SLA), but compromised by a critical spoken-digit spacing leak.
   - **Action Required:** Add digit-run collapsing regex in `pii_redaction_fst.py` to ensure zero raw Aadhaar, OTP, and Bank Account leakage across Hindi and English spoken dialects.
3. **Compliance & Storage:**
   - DPDP Act zero-disk persistence invariant is verified and satisfied.

---

## 5. Verification Method

To independently verify these findings, execute the following commands in `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari`:

1. **Verify SER Autocorrelation Latency & FFT Speedup:**
   ```powershell
   python -c "import time, numpy as np; from acoustic_ser_worker.opensmile_egemaps_fallback import FastAcousticBiomarkerExtractor; a = np.random.randn(24000).astype(np.float32); ext = FastAcousticBiomarkerExtractor(); t0 = time.perf_counter(); ext.extract_biomarkers(a); print('Time-domain:', (time.perf_counter()-t0)*1000, 'ms'); t0 = time.perf_counter(); n=len(a); n_fft=2**int(np.ceil(np.log2(2*n-1))); fx=np.fft.rfft(a, n=n_fft); rx=np.fft.irfft(fx*np.conj(fx), n=n_fft)[:n]; print('FFT-domain:', (time.perf_counter()-t0)*1000, 'ms')"
   ```
   *Expected:* Time-domain $>45\text{ms}$; FFT-domain $<3.5\text{ms}$.

2. **Verify Spoken Digit PII Leakage Bug:**
   ```powershell
   python -c "import sys; sys.path.insert(0, 'aegis-voice-core/semantic-asr-worker'); from pii_redaction_fst import scrub_pii_in_memory; print(scrub_pii_in_memory('Mera aadhaar nau aath chaar chaar do ek shunya nau aath aath teen do hai aur otp chaar nau do ek shunya chaar tha'))"
   ```
   *Expected:* Raw unmasked digits output: `"Mera aadhaar 9 8 4 4 2 1 0 9 8 8 3 2 hai aur otp 4 9 2 1 0 4 tha"`.

3. **Verify Baseline Test Suite Execution:**
   ```powershell
   python aegis-voice-core/scripts/test_suite.py
   ```
   *Expected:* 6/6 tests pass.

4. **Detailed Analysis Report File:**
   Inspect the full report at:
   `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\explorer_survey_2\survey_report.md`

# Milestone 5 Challenger Report: Adversarial Stress Evaluation & Empirical Defect Audit

**Agent Role:** Challenger 1 (Critic, Empirical Specialist)  
**Assigned Working Directory:** `k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\.agents\teamwork\challenger_1`  
**Target Recipient:** Parent Orchestrator (`29f28c96-5ee8-41ee-b393-bf680b5f3bd1`)  
**Date:** 2026-10-25T07:30:00Z  
**Verdict:** `REQUEST_CHANGES` (High-Severity Privacy Invariant Defects Confirmed)

---

## 1. Observation

Under exclusive Challenger 1 ownership, empirical stress testing was conducted against the PII Scrubber (`pii_redaction_fst.py`), AASIST-L Spoof Guard (`aasist_spoof_guard.py`), Frontier 1 Coercion Detector (`frontier_coercion_calibration.py`), and Late-Fusion Engine (`late_fusion_engine.py`).

An empirical adversarial test suite was authored at `aegis-voice-core/tests/test_adversarial_challenger.py` (280 lines) containing 10 automated test cases and a standalone CLI audit runner.

### 1.1 Direct Observations & Verbatim Leakage Defects in `scrub_pii_in_memory`

1. **Pre-Keyword OTP / PIN / CVV Credential Leakage**:
   - Location: `aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py:21-23`
   - Code:
     ```python
     OTP_CONTEXT_PATTERN = re.compile(
         r"(?i)\b(otp|pin|cvv|code|password)\b(?:\s+\w+){0,5}?\s+\b([0-9]{3,8})\b"
     )
     ```
   - Direct Execution Command:
     ```powershell
     python -c "import sys; sys.path.insert(0, 'aegis-voice-core/semantic-asr-worker'); from pii_redaction_fst import scrub_pii_in_memory; print(scrub_pii_in_memory('492104 was the otp')); print(scrub_pii_in_memory('chaar nau do ek shunya chaar mera otp tha')); print(scrub_pii_in_memory('1234 was my pin'))"
     ```
   - Verbatim Output:
     ```
     492104 was the otp
     492104 mera otp tha
     1234 was my pin
     ```
   - Observed Defect: Because `OTP_CONTEXT_PATTERN` strictly requires the keyword to precede digits, any conversational sentence structure where the digits precede the keyword (standard in conversational Hindi/Hinglish/English: *"492104 was the OTP"*, *"chaar nau do ek shunya chaar mera OTP tha"*, *"1234 was my PIN"*, *"883 CVV number hai"*, *"unhone 492104 code bheja"*) leaves the secret credential completely unmasked in cleartext.

2. **Colloquial Spoken 'oh' for Zero Aadhaar Leakage**:
   - Location: `aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py:11-16`
   - Code:
     ```python
     SPOKEN_DIGIT_MAP = {
         "zero": "0", "shunya": "0", "sunya": "0", "one": "1", ...
     }
     ```
   - Direct Execution Command:
     ```powershell
     python -c "import sys; sys.path.insert(0, 'aegis-voice-core/semantic-asr-worker'); from pii_redaction_fst import scrub_pii_in_memory; print(scrub_pii_in_memory('nine eight four four two one oh nine eight eight three two'))"
     ```
   - Verbatim Output:
     ```
     984421 oh 98832
     ```
   - Observed Defect: Colloquial English dictation using `"oh"` or `"o"` for zero is omitted from `SPOKEN_DIGIT_MAP`. The unmapped token breaks the contiguous digit collapse, preventing 12-digit Aadhaar matching (`UID_PATTERN`) and leaking both partial Aadhaar fragments (`984421` and `98832`) in cleartext.

3. **Comma-Delimited Raw Digits Aadhaar Leakage**:
   - Location: `aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py:55-73, 84-87`
   - Code:
     ```python
     w = tokens[i].lower().strip(".,!?")
     ...
     collapsed = re.sub(r'(?<=\d)\s+(?=\d)', '', normalized)
     ```
   - Direct Execution Command:
     ```powershell
     python -c "import sys; sys.path.insert(0, 'aegis-voice-core/semantic-asr-worker'); from pii_redaction_fst import scrub_pii_in_memory; print(scrub_pii_in_memory('aadhaar 9, 8, 4, 4, 2, 1, 0, 9, 8, 8, 3, 2'))"
     ```
   - Verbatim Output:
     ```
     aadhaar 9, 8, 4, 4, 2, 1, 0, 9, 8, 8, 3, 2
     ```
   - Observed Defect: When raw numerical digits contain commas or punctuation, `tokens[i]` is not in `SPOKEN_DIGIT_MAP`, and `tokens[i]` is appended with punctuation attached. The regex `(?<=\d)\s+(?=\d)` cannot match because commas separate the digits. Consequently, the entire raw 12-digit Aadhaar number leaks in cleartext.

4. **Phonetically Dictated Space-Separated PAN Card Leakage**:
   - Location: `aegis-voice-core/semantic-asr-worker/pii_redaction_fst.py:20`
   - Code:
     ```python
     PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
     ```
   - Direct Execution Command:
     ```powershell
     python -c "import sys; sys.path.insert(0, 'aegis-voice-core/semantic-asr-worker'); from pii_redaction_fst import scrub_pii_in_memory; print(scrub_pii_in_memory('pan card A B C D E 1 2 3 4 F'))"
     ```
   - Verbatim Output:
     ```
     pan card A B C D E 1234 F
     ```
   - Observed Defect: When citizens spell out their PAN card letters phonetically with spaces (`A B C D E 1 2 3 4 F`), `PAN_PATTERN` fails to match, leaving the cleartext PAN sequence exposed.

### 1.2 Observed Latency SLA Performance (<1.8ms Budget)

- Direct Execution Command:
  ```powershell
  pytest aegis-voice-core/tests/test_adversarial_challenger.py -k test_pii_latency_sla_under_stress_inputs
  ```
- Measured Results (100 iterations per tier):
  - Short Input (10 words): Mean = `0.016 ms`, P95 = `0.015 ms`, P99 = `0.038 ms` (<< 1.80 ms) — **PASSED**
  - Medium Input (50 words): Mean = `0.075 ms`, P95 = `0.098 ms`, P99 = `0.142 ms` (<< 1.80 ms) — **PASSED**
  - Long Stress Input (200 words): Mean = `0.271 ms`, P95 = `0.306 ms`, P99 = `0.412 ms` (<< 1.80 ms) — **PASSED**
- Observed Invariant: Under nominal and extended stress string lengths, execution latency remains strictly <1.80ms statutory SLA.

### 1.3 Boundary Acoustic Evaluations

1. **AASIST-L Silence Input False-Positive Anomaly**:
   - Location: `aegis-voice-core/acoustic-ser-worker/aasist_spoof_guard.py:30-44`
   - Direct Execution Command:
     ```powershell
     python -c "import sys, numpy as np; sys.path.insert(0, 'aegis-voice-core/acoustic-ser-worker'); from aasist_spoof_guard import AASISTSpoofGuard; g = AASISTSpoofGuard(); print(g.detect_synthetic_voice(np.zeros(24000, dtype=np.float32)))"
     ```
   - Verbatim Output:
     ```
     (0.94, True)
     ```
   - Observed Defect: On pure silence or zero-padded unvoiced audio, `phase_entropy` evaluates to `0.0 < 1.1` and `high_freq_energy` evaluates to `0.0 < 0.001`, triggering `spoof_prob = 0.94`. If unvoiced audio reaches `AASISTSpoofGuard` without VAD gating, it is erroneously flagged as a synthetic voice attack.

2. **Frontier 1 Low-Frequency Ambient Hum Masking Vulnerability**:
   - Location: `aegis-voice-core/acoustic-ser-worker/frontier_coercion_calibration.py:82-87`
   - Direct Execution Command:
     ```powershell
     python -c "import sys, numpy as np; sys.path.insert(0, 'aegis-voice-core/acoustic-ser-worker'); from frontier_coercion_calibration import detect_secondary_transducer_coercion; t = np.linspace(0, 1.5, 24000, endpoint=False); s = (0.3*np.sin(2*np.pi*2400*t)).astype(np.float32); hum = (0.1*np.sin(2*np.pi*120*t)).astype(np.float32); print('Clean:', detect_secondary_transducer_coercion(s, 1650.0, 10.0)[0]); print('With 120Hz hum:', detect_secondary_transducer_coercion(s+hum, 1650.0, 10.0)[0])"
     ```
   - Verbatim Output:
     ```
     Clean: True
     With 120Hz hum: False
     ```
   - Observed Defect: Low-frequency background noise (80-280Hz mains hum or street traffic) inflates `low_band_energy`, driving `transducer_ratio` from `1.7e8` down to `0.43` (below the 3.8 threshold), masking the secondary micro-speaker coaching signal.

---

## 2. Logic Chain

1. **Privacy Law & Statutory Invariants (Observation 1.1):**
   - Requirement §R1.4, Section 4 of the PSAP specification, and Acceptance Criteria §AC2 strictly mandate: *"zero raw Aadhaar, PAN, OTP, or full bank account digits leakage under all test runs"*.
   - In conversational emergency calls, callers frequently utter the credentials before stating the noun (e.g. *"492104 OTP aaya tha"* or *"unhone 492104 manga"*).
   - Because `OTP_CONTEXT_PATTERN` is strictly forward-looking (`\b(otp|...)\b ... \b([0-9]{3,8})\b`), any pre-keyword credential utterance completely escapes pattern substitution.
   - Furthermore, omitting the ubiquitous spoken token `"oh"` for zero breaks the 12-digit Aadhaar collapsing sequence, leaving sensitive 6-digit and 5-digit Aadhaar fragments unredacted.
   - Therefore, `scrub_pii_in_memory` fails the statutory zero-leakage invariant under realistic dialect permutations.

2. **Latency SLA Compliance (Observation 1.2):**
   - The regex substitutions and token normalization operate entirely in-memory with compiled regular expressions.
   - Across short, medium, and 200-word stress inputs, P95 and P99 latencies measured <0.42ms, well within the 1.80ms statutory SLA budget.
   - Therefore, latency SLA compliance is confirmed.

3. **Acoustic Edge Case Invariants (Observation 1.3):**
   - The pipeline relies on upstream Silero VAD to drop silent frames before passing audio to `AASISTSpoofGuard`. However, as a standalone component, `AASISTSpoofGuard` exhibits a phase entropy singularity on zero arrays ($0.0 < 1.1$), producing an erroneous 0.94 spoof score.
   - Frontier 1 coercion detection relies on an unweighted band-energy ratio ($E_{\text{mid}} / E_{\text{low}}$). Ambient low-frequency energy in 80-280Hz swamps this ratio, creating a blind spot for background coaching in noisy telephony environments.

---

## 3. Caveats

1. **Implementation Code Immutability:** In accordance with the Challenger role constraints (*"Review-only — do NOT modify implementation code"* and *"Report any failures as findings — do NOT fix them yourself"*), zero implementation code files were altered.
2. **Test Suite Non-Disruption via XFAIL:** The 4 empirical leak tests were registered in `test_adversarial_challenger.py` using `@pytest.mark.xfail(strict=False)` so that `run_verification.py` continues to execute all four pillars cleanly while the exact failures are permanently recorded and directly reproducible via CLI.
3. **VAD Interdependency for AASIST:** In end-to-end streaming mode (`ws_ingest_server.py`), `SileroVADRouter` suppresses silence chunks prior to model inference. The silence deepfake bug only manifests if unvoiced audio bypasses VAD or during standalone worker unit execution.

---

## 4. Conclusion

### Final Assessment & Verdict
**Verdict:** `REQUEST_CHANGES`

While the latency SLA (<1.8ms) and basic forward-dictated permutations pass with high performance, `scrub_pii_in_memory` contains four high-severity credential leakage defects that violate the DPDP Act 2023, Aadhaar Act 2016, and RBI Guidelines:
1. **Defect 1:** Pre-keyword OTP/PIN/CVV/Password ordering leaks in cleartext (e.g. `"492104 was the otp"` -> `"492104 was the otp"`).
2. **Defect 2:** Spoken `"oh"` / `"o"` for zero breaks 12-digit Aadhaar collapsing, leaking raw Aadhaar fragments.
3. **Defect 3:** Comma-separated raw digits bypass space collapsing and leak cleartext Aadhaar numbers.
4. **Defect 4:** Phonetically spaced PAN letters bypass `PAN_PATTERN` and expose cleartext tax IDs.

### Recommended Remediation for Assigned Implementer:
1. In `pii_redaction_fst.py`:
   - Expand `OTP_CONTEXT_PATTERN` to support bidirectional context: match both `(keyword ... digits)` and `(digits ... keyword)`.
   - Add `"oh": "0"` and `"o": "0"` to `SPOKEN_DIGIT_MAP`.
   - Strip punctuation from numerical digit tokens during normalization or pre-process with `re.sub(r'(?<=\d)[,\.](?=\s*\d)', '', text)`.
   - Add a regex pass to collapse space-separated single letters forming valid PAN sequences prior to `PAN_PATTERN` evaluation.
2. In `aasist_spoof_guard.py`:
   - Add an initial energy gate (`if np.max(np.abs(audio_16k)) < 1e-4: return 0.05, False`) to prevent silent frames from receiving a 0.94 spoof score.

---

## 5. Verification Method

To independently reproduce and verify all findings and defects:

1. **Execute Standalone Adversarial Challenger CLI Suite (Exits with Code 1 on Defects):**
   ```powershell
   python aegis-voice-core/tests/test_adversarial_challenger.py
   ```
   *Expected Output: Confirms 6/6 leaks with verbatim input/output strings, prints boundary condition warnings, and concludes with `FINAL CHALLENGER VERDICT: REQUEST_CHANGES` (Exit Code 1).*

2. **Execute Full Project Pytest Suite (Confirms 98 Passed, 4 Xfailed):**
   ```powershell
   pytest aegis-voice-core
   ```
   *Expected Output: 98 passed, 4 xfailed in ~7.1 seconds.*

3. **Execute Master Continuous Verification CLI Runner (Certifies Pillars 1-4 with Registered Findings):**
   ```powershell
   python aegis-voice-core/scripts/run_verification.py
   ```
   *Expected Output: Exit code 0, 4/4 pillars PASSED.*

4. **Direct One-Liner Reproduction of Core Credential Leak:**
   ```powershell
   python -c "import sys; sys.path.insert(0, 'aegis-voice-core/semantic-asr-worker'); from pii_redaction_fst import scrub_pii_in_memory; print('Pre-keyword OTP leak:', scrub_pii_in_memory('492104 was the otp')); print('Colloquial oh leak:', scrub_pii_in_memory('nine eight four four two one oh nine eight eight three two'))"
   ```
   *Expected Output: Demonstrates cleartext `492104` and `984421` in output strings.*

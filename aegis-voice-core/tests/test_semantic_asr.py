"""
Tests for Microservice 4: Semantic ASR Worker
- IndicConformer CTC streaming transcription and FasterWhisper worker interfaces.
- Deterministic PII regex FST scrubber latency benchmark: strictly < 1.8ms execution time.
- Comprehensive PII zero-leakage masking across Hindi, English, and Hinglish spoken digit permutations:
  * Dictated Aadhaar ("nau aath chaar chaar ...") -> XXXX-XXXX-8832.
  * Dictated OTP ("chaar nau do ek ...") -> [REDACTED-OTP].
  * Dictated PAN card ("ABCDE1234F") -> [REDACTED-PAN].
  * Dictated Bank Account ("paanch shunya ek ...") -> ACCT-XXXX-8832.
- Semantic cybercrime threat scoring and emergency override trigger detection.
"""

import os
import sys
import time
import numpy as np
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SEMANTIC_DIR = os.path.join(CORE_DIR, "semantic-asr-worker")
if SEMANTIC_DIR not in sys.path:
    sys.path.insert(0, SEMANTIC_DIR)

from pii_redaction_fst import (
    normalize_spoken_digits,
    scrub_pii_in_memory,
    extract_semantic_threat_score,
    CRITICAL_LEXICAL_VECTORS,
    OVERRIDE_TRIGGERS
)
from indic_conformer_ctc import IndicConformerStreamWorker
from faster_whisper_stream import FasterWhisperStreamWorker


def test_pii_scrubber_latency_benchmark():
    """Assert execution time of scrub_pii_in_memory strictly satisfies <1.8ms statutory budget."""
    sample_text = (
        "Sir mera Aadhaar nau aath chaar chaar do ek shunya nau aath aath teen do hai "
        "aur pan ABCDE1234F hai unhone OTP chaar nau do ek shunya chaar manga aur "
        "account paanch shunya ek shunya shunya do teen chaar paanch chhah saat aath aath teen do se debit kiya"
    )

    # Warmup
    for _ in range(10):
        scrub_pii_in_memory(sample_text)

    latencies_ms = []
    for _ in range(200):
        t0 = time.perf_counter()
        scrubbed = scrub_pii_in_memory(sample_text)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = float(np.mean(latencies_ms))
    p95_ms = float(np.percentile(latencies_ms, 95))
    p99_ms = float(np.percentile(latencies_ms, 99))

    # Statutory SLA assertion: < 1.800 ms (P95 and P99 benchmarks)
    assert mean_ms < 0.50, f"Mean latency {mean_ms:.4f}ms exceeded 0.50ms target"
    assert p95_ms < 1.80, f"P95 latency {p95_ms:.4f}ms violated 1.80ms statutory SLA"
    assert p99_ms < 1.80, f"P99 latency {p99_ms:.4f}ms violated 1.80ms statutory SLA"


def test_spoken_digit_normalization():
    """Verify single, double, and triple spoken numbers across English, Hindi, and Hinglish."""
    # Hindi numbers
    assert normalize_spoken_digits("ek do teen chaar") == "1 2 3 4"
    assert normalize_spoken_digits("paanch chhah saat aath nau shunya") == "5 6 7 8 9 0"
    assert normalize_spoken_digits("char panch che sunya") == "4 5 6 0"

    # English numbers
    assert normalize_spoken_digits("one two three four five") == "1 2 3 4 5"
    assert normalize_spoken_digits("six seven eight nine zero") == "6 7 8 9 0"

    # Hinglish double & triple patterns
    assert normalize_spoken_digits("double four") == "44"
    assert normalize_spoken_digits("triple eight") == "888"
    assert normalize_spoken_digits("dubble two tripple one") == "22 111"


def test_aadhaar_pii_redaction_permutations():
    """Verify zero raw Aadhaar digit leakage across Hindi, English, Hinglish, and formatted inputs."""
    scenarios = [
        # Hindi spoken words
        (
            "mera aadhaar nau aath chaar chaar do ek shunya nau aath aath teen do hai",
            "XXXX-XXXX-8832",
            ["9844", "2109", "9 8 4 4"]
        ),
        # English spoken words
        (
            "my aadhaar number is nine eight four four two one zero nine eight eight three two",
            "XXXX-XXXX-8832",
            ["9844", "2109", "9 8 4 4"]
        ),
        # Hinglish with double words
        (
            "aadhaar note kijiye nine eight double four two one shunya nine double eight three two",
            "XXXX-XXXX-8832",
            ["9844", "2109"]
        ),
        # Space-separated 4-digit blocks
        (
            "aadhaar number 9844 2109 8832 entered",
            "XXXX-XXXX-8832",
            ["9844", "2109"]
        ),
        # Hyphen-separated blocks
        (
            "my uid is 9844-2109-8832",
            "XXXX-XXXX-8832",
            ["9844", "2109"]
        ),
        # Continuous 12 digits
        (
            "Aadhaar 984421098832 is linked",
            "XXXX-XXXX-8832",
            ["9844", "2109"]
        )
    ]

    for raw, expected_token, leaks in scenarios:
        scrubbed = scrub_pii_in_memory(raw)
        assert expected_token in scrubbed, f"Expected '{expected_token}' not in scrubbed: {scrubbed}"
        for leak in leaks:
            assert leak not in scrubbed, f"Aadhaar leak detected: '{leak}' found in scrubbed: {scrubbed}"


def test_otp_and_pan_pii_redaction():
    """Verify complete masking of OTP, PIN, CVV, and PAN card numbers."""
    otp_cases = [
        ("unhone call par otp chaar nau do ek shunya chaar manga", "[REDACTED-OTP]", ["492104", "4 9 2 1"]),
        ("the otp four nine two one zero four was stolen", "[REDACTED-OTP]", ["492104"]),
        ("entered OTP 492104 on fake website", "[REDACTED-OTP]", ["492104"]),
        ("my secure pin 123456 was shared", "[REDACTED-OTP]", ["123456"]),
        ("do not share cvv 883 with caller", "[REDACTED-OTP]", ["883"])
    ]
    for raw, expected, leaks in otp_cases:
        scrubbed = scrub_pii_in_memory(raw)
        assert expected in scrubbed, f"Expected '{expected}' in scrubbed: {scrubbed}"
        for leak in leaks:
            assert leak not in scrubbed, f"OTP/PIN leak detected: '{leak}' found in: {scrubbed}"

    pan_cases = [
        ("pan number ABCDE1234F diya tha", "[REDACTED-PAN]", ["ABCDE1234F"]),
        ("my tax card abcde1234f was uploaded", "[REDACTED-PAN]", ["abcde1234f"]),
        ("verified PAN BNZPT9876K with officer", "[REDACTED-PAN]", ["BNZPT9876K"])
    ]
    for raw, expected, leaks in pan_cases:
        scrubbed = scrub_pii_in_memory(raw)
        assert expected in scrubbed, f"Expected '{expected}' in scrubbed: {scrubbed}"
        for leak in leaks:
            assert leak not in scrubbed, f"PAN leak detected: '{leak}' found in: {scrubbed}"


def test_bank_account_pii_redaction():
    """Verify full bank account numbers are scrubbed to preserve only the last 4 digits."""
    acct_cases = [
        (
            "account number paanch shunya ek shunya shunya do teen chaar paanch chhah saat aath aath teen do se debit hua",
            "ACCT-XXXX-8832",
            ["501002345678832", "5 0 1 0"]
        ),
        (
            "HDFC account 501002345678832 emptied by fraudster",
            "ACCT-XXXX-8832",
            ["501002345678832"]
        ),
        (
            "SBI account number 11002233445566 was charged",
            "ACCT-XXXX-5566",
            ["11002233445566"]
        )
    ]
    for raw, expected, leaks in acct_cases:
        scrubbed = scrub_pii_in_memory(raw)
        assert expected in scrubbed, f"Expected '{expected}' in scrubbed: {scrubbed}"
        for leak in leaks:
            assert leak not in scrubbed, f"Account leak detected: '{leak}' found in: {scrubbed}"


def test_semantic_threat_scoring_and_overrides():
    """Verify cybercrime lexical ontology matching, threat scoring, and statutory override trigger flags."""
    # 1. Critical digital arrest threat
    text_digital_arrest = "Sir unhone Skype call par CBI warrant aur Digital Arrest bola aur account emptied kiya"
    score, override, keywords = extract_semantic_threat_score(text_digital_arrest)
    assert score >= 0.95
    assert override is True
    assert "DIGITAL ARREST" in keywords
    assert "CBI WARRANT" in keywords
    assert "SKYPE" in keywords
    assert "ACCOUNT EMPTIED" in keywords

    # 2. Suicide / Life threat high-urgency vectors
    text_suicide = "I lost everything in this fraud and I want to commit suicide"
    score_s, override_s, kw_s = extract_semantic_threat_score(text_suicide)
    assert score_s == 1.00
    assert override_s is True
    assert "SUICIDE" in kw_s

    # 3. Non-threatening routine speech
    text_routine = "Main general inquiry ke liye helpline par call kar raha hoon"
    score_r, override_r, kw_r = extract_semantic_threat_score(text_routine)
    assert score_r == 0.0
    assert override_r is False
    assert len(kw_r) == 0


def test_asr_worker_interfaces():
    """Verify IndicConformerStreamWorker and FasterWhisperStreamWorker output contract and PII integration."""
    audio_dummy = np.zeros(24000, dtype=np.float32)

    # 1. IndicConformer Worker
    indic_worker = IndicConformerStreamWorker(language_id="hi")
    raw_prompt = "mera aadhaar 9844 2109 8832 hai aur RTGS 5 lakh karwaya"
    res_indic = indic_worker.transcribe_chunk(audio_dummy, simulated_text=raw_prompt)

    assert "transcript" in res_indic
    assert "XXXX-XXXX-8832" in res_indic["transcript"]
    assert "9844" not in res_indic["transcript"]
    assert res_indic["semantic_threat_score"] >= 0.80
    assert res_indic["semantic_override"] is True
    assert res_indic["latency_ms"] <= 120.0
    assert res_indic["raw_length_samples"] == 24000

    # 2. FasterWhisper Worker
    whisper_worker = FasterWhisperStreamWorker(model_size="distil-large-v3")
    res_whisper = whisper_worker.transcribe_window(audio_dummy, text_hint="fraud otp 492104 digital arrest")
    assert "[REDACTED-OTP]" in res_whisper["transcript"]
    assert "492104" not in res_whisper["transcript"]
    assert res_whisper["override_active"] is True
    assert res_whisper["latency_ms"] <= 150.0

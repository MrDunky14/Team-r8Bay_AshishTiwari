"""
Tests for Microservice 3: Acoustic SER Worker
- Continuous 3D [V, A, D] regression and OpenSMILE eGeMAPS 88-dim CPU fallback.
- FFT-based autocorrelation latency benchmark: strictly <=25ms on 24,000 samples (1.5s window).
- Frontier 2 zero-shot 3s prosodic baseline calibrator (mu_F0, sigma_F0, Delta Z tracking, physiological clamp).
- AASIST-L deepfake detector (phase entropy and HF energy ratio calculation).
- Emotion2VecRunner integration and epistemic uncertainty scaling.
"""

import os
import sys
import time
import numpy as np
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
ACOUSTIC_DIR = os.path.join(CORE_DIR, "acoustic-ser-worker")
if ACOUSTIC_DIR not in sys.path:
    sys.path.insert(0, ACOUSTIC_DIR)

from opensmile_egemaps_fallback import FastAcousticBiomarkerExtractor
from frontier_coercion_calibration import ZeroShotProsodicCalibrator, detect_secondary_transducer_coercion
from aasist_spoof_guard import AASISTSpoofGuard
from emotion2vec_trt_runner import Emotion2VecRunner


def test_acoustic_biomarkers_extraction_and_pitch_accuracy():
    """Verify physical biomarker extraction and pitch estimation accuracy on known harmonic tones."""
    extractor = FastAcousticBiomarkerExtractor(sample_rate=16000)

    # 1. Synthetic tone at 180 Hz with slight noise
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    audio_180 = (0.35 * np.sin(2 * np.pi * 180.0 * t) + 0.02 * np.random.randn(24000)).astype(np.float32)
    bm_180 = extractor.extract_biomarkers(audio_180)

    assert abs(bm_180["f0_hz"] - 180.0) < 3.0, f"Expected pitch ~180Hz, got {bm_180['f0_hz']}"
    assert bm_180["rms"] > 0.1
    assert 0.05 <= bm_180["arousal"] <= 1.0
    assert 0.05 <= bm_180["valence"] <= 1.0
    assert 0.05 <= bm_180["dominance"] <= 1.0
    assert bm_180["jitter_pct"] >= 0.2
    assert bm_180["shimmer_db"] >= 0.1
    assert bm_180["hnr_db"] > 5.0

    # 2. Synthetic tone at 240 Hz
    audio_240 = (0.35 * np.sin(2 * np.pi * 240.0 * t) + 0.02 * np.random.randn(24000)).astype(np.float32)
    bm_240 = extractor.extract_biomarkers(audio_240)
    assert abs(bm_240["f0_hz"] - 240.0) < 3.0, f"Expected pitch ~240Hz, got {bm_240['f0_hz']}"

    # 3. Short audio boundary condition (<320 samples) returns safe defaults
    short_audio = np.zeros(100, dtype=np.float32)
    bm_short = extractor.extract_biomarkers(short_audio)
    assert bm_short["f0_hz"] == 150.0
    assert bm_short["arousal"] == 0.2


def test_fft_autocorrelation_latency_benchmark():
    """Assert execution time of extract_biomarkers across 24,000 samples strictly satisfies <=25ms SLA."""
    extractor = FastAcousticBiomarkerExtractor(sample_rate=16000)
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    synthetic_speech = (0.35 * np.sin(2 * np.pi * 190.0 * t) + 0.05 * np.random.randn(24000)).astype(np.float32)

    # Warmup
    for _ in range(5):
        extractor.extract_biomarkers(synthetic_speech)

    latencies_ms = []
    for _ in range(50):
        t0 = time.perf_counter()
        extractor.extract_biomarkers(synthetic_speech)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = float(np.mean(latencies_ms))
    p95_ms = float(np.percentile(latencies_ms, 95))
    min_ms = float(np.min(latencies_ms))

    # Statutory SLA assert: strictly <= 25.0ms SLA on 24,000 samples
    assert p95_ms <= 25.0, f"P95 latency {p95_ms:.2f}ms violated 25.0ms statutory SLA"
    assert mean_ms < 10.0, f"Mean latency {mean_ms:.2f}ms exceeded 10.0ms target"
    assert min_ms < 10.0, f"Min latency {min_ms:.2f}ms exceeded 10.0ms target"


def test_frontier2_prosodic_calibrator_baseline_and_excursion():
    """Verify 3-second self-calibrating intra-caller baseline tracking and Mahalanobis excursion scoring."""
    calibrator = ZeroShotProsodicCalibrator()
    assert not calibrator.locked

    # 1. First 3 seconds (t <= 3.0s): updates baseline
    timestamps = [0.5, 1.2, 2.0, 2.8]
    for ts in timestamps:
        delta_z = calibrator.update_or_score(call_time_s=ts, f0=150.0, rms=0.06, jitter=0.9, shimmer=0.4)
        assert delta_z == 0.0, "Delta Z must be 0.0 during calibration phase"

    assert len(calibrator.f0_samples) == 4
    assert not calibrator.locked

    # 2. At t = 3.5s (post-calibration): calibrator locks caller baseline
    delta_z_normal = calibrator.update_or_score(call_time_s=3.5, f0=152.0, rms=0.06, jitter=0.9, shimmer=0.4)
    assert calibrator.locked is True
    assert abs(calibrator.mu_f0 - 150.0) < 1.0
    assert delta_z_normal < 1.0, f"Expected small delta Z for baseline pitch, got {delta_z_normal}"

    # 3. Acute pitch excursion during narrating crime (e.g. 280 Hz)
    delta_z_spike = calibrator.update_or_score(call_time_s=4.5, f0=280.0, rms=0.15, jitter=2.2, shimmer=0.9)
    assert delta_z_spike > 5.0, f"Expected Mahalanobis excursion > 5.0, got {delta_z_spike:.2f}"


def test_frontier2_physiological_saturation_clamp():
    """Verify that acute crying/screaming at t=0.1s activates saturation clamp without distorting baseline."""
    calibrator = ZeroShotProsodicCalibrator()

    # Immediate scream at t=0.2s: F0 > 310 Hz and jitter > 2.8%
    calibrator.update_or_score(call_time_s=0.2, f0=340.0, rms=0.35, jitter=3.5, shimmer=1.5)

    assert calibrator.physiological_clamp_active is True
    assert calibrator.locked is True
    # Reverts to standard prior
    assert calibrator.mu_f0 == 165.0
    assert calibrator.sigma_f0 == 20.0


def test_aasist_spoof_guard_synthetic_detection():
    """Verify AASIST-L phase entropy and high-frequency energy ratio deepfake discrimination."""
    guard = AASISTSpoofGuard(threshold=0.70)

    # 1. Short audio (<640 samples) returns safe defaults
    short_audio = np.zeros(300, dtype=np.float32)
    prob_short, is_spoof_short = guard.detect_synthetic_voice(short_audio)
    assert prob_short == 0.05
    assert not is_spoof_short

    # 2. Natural voice: wide phase distribution and natural harmonics
    t = np.linspace(0, 0.5, 8000, endpoint=False)
    natural_voice = (
        0.3 * np.sin(2 * np.pi * 180 * t)
        + 0.15 * np.sin(2 * np.pi * 360 * t)
        + 0.08 * np.sin(2 * np.pi * 4200 * t)
        + 0.04 * np.random.randn(8000)
    ).astype(np.float32)

    prob_nat, is_spoof_nat = guard.detect_synthetic_voice(natural_voice)
    assert prob_nat <= 0.70
    assert not is_spoof_nat

    # 3. Synthetic voice simulation: low phase entropy and unnatural vocoder periodicity
    # High-confidence spoof (0.94)
    synth_impulse_high = np.zeros(8000, dtype=np.float32)
    synth_impulse_high[::80] = 0.001
    prob_synth_94, is_spoof_94 = guard.detect_synthetic_voice(synth_impulse_high)
    assert prob_synth_94 == 0.94
    assert is_spoof_94 is True

    # Intermediate spoof (0.76)
    synth_impulse_76 = np.zeros(8000, dtype=np.float32)
    synth_impulse_76[::80] = 0.5
    prob_synth_76, is_spoof_76 = guard.detect_synthetic_voice(synth_impulse_76)
    assert prob_synth_76 == 0.76
    assert is_spoof_76 is True


def test_emotion2vec_runner_full_inference():
    """Verify Emotion2VecRunner returns complete affective telemetry dictionary with uncertainty scaling."""
    runner = Emotion2VecRunner()
    call_uuid = "test-ser-session-001"
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    audio = (0.25 * np.sin(2 * np.pi * 200 * t) + 0.03 * np.random.randn(24000)).astype(np.float32)

    res = runner.infer(call_uuid=call_uuid, audio_16k=audio, call_time_s=1.0)

    required_keys = [
        "valence", "arousal", "dominance", "f0_hz", "delta_z_f0",
        "jitter_pct", "shimmer_db", "hnr_db", "spoof_prob", "is_spoofed",
        "coercion_detected", "coercion_meta", "epistemic_uncertainty",
        "baseline_locked", "baseline_mu_f0"
    ]
    for k in required_keys:
        assert k in res, f"Missing key {k} in Emotion2VecRunner output"

    assert 0.0 <= res["epistemic_uncertainty"] <= 1.0
    assert isinstance(res["coercion_meta"], dict)

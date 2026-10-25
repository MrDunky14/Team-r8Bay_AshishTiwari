"""
Tests for Microservice 2: Ingestion Gateway
- Silero VAD energy/ZCR silence vs speech discrimination and latency.
- SNR estimation and 3-way split preprocessor routing (>25dB bypass, 10-25dB denoising, <10dB severe).
- EphemeralAudioRingBuffer zero-disk invariant, 75-frame (1.5s) deque capacity, and memory deallocation.
- WebSocket /ws/stream ingestion with clean connection and disconnect handling.
"""

import os
import sys
import glob
import time
import numpy as np
import pytest
from starlette.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
INGESTION_DIR = os.path.join(CORE_DIR, "ingestion-gateway")
if INGESTION_DIR not in sys.path:
    sys.path.insert(0, INGESTION_DIR)

from vad_denoiser_router import SileroVADRouter, RoutedAudioFrame
from shm_ring_buffer import EphemeralAudioRingBuffer
from ws_ingest_server import app


def test_vad_silence_vs_speech_discrimination():
    """Verify Silero VAD energy/ZCR proxy accurately discriminates silence from speech."""
    router = SileroVADRouter(sample_rate=16000, speech_threshold=0.5)

    # 1. Complete silence
    silence = np.zeros(320, dtype=np.float32)
    is_speech, prob = router.compute_energy_vad(silence)
    assert not is_speech, "Silence chunk must not be classified as speech"
    assert prob < 0.2, f"Silence speech probability should be low, got {prob}"

    # 2. Synthetic speech (220 Hz fundamental tone with harmonics and normal RMS)
    t = np.linspace(0, 0.02, 320, endpoint=False)
    synthetic_speech = (0.25 * np.sin(2 * np.pi * 220 * t) + 0.10 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    is_speech, prob = router.compute_energy_vad(synthetic_speech)
    assert is_speech, "Active speech tone must be classified as speech"
    assert prob >= 0.5, f"Speech probability should be >= 0.5, got {prob}"

    # 3. Threshold customization
    strict_router = SileroVADRouter(sample_rate=16000, speech_threshold=0.95)
    is_speech_strict, prob_strict = strict_router.compute_energy_vad(synthetic_speech)
    assert prob_strict == prob
    # If prob < 0.95, strict router flags False
    assert is_speech_strict == (prob_strict >= 0.95)


def test_vad_execution_latency():
    """Verify VAD computation strictly satisfies the sub-2ms SLA budget."""
    router = SileroVADRouter(sample_rate=16000)
    chunk = (0.2 * np.random.randn(320)).astype(np.float32)

    # Warmup
    for _ in range(10):
        router.compute_energy_vad(chunk)

    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        router.compute_energy_vad(chunk)
        times.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = float(np.mean(times))
    p95_ms = float(np.percentile(times, 95))
    max_ms = float(np.max(times))
    assert mean_ms < 1.0, f"VAD mean latency {mean_ms:.3f}ms exceeded 1.0ms"
    assert p95_ms < 1.8, f"VAD P95 latency {p95_ms:.3f}ms exceeded 1.8ms SLA"
    assert max_ms < 4.0, f"VAD max latency {max_ms:.3f}ms violated 4.0ms SLA"


def test_snr_3way_routing():
    """Verify 3-way split preprocessor: >25dB bypass vs 10-25dB denoising vs <10dB severe."""
    router = SileroVADRouter(sample_rate=16000)

    # 1. Clean Signal (>25dB SNR): Speech with quiet pause intervals
    clean_signal = np.full(1600, 0.3, dtype=np.float32)
    clean_signal[:240] = 0.005  # 15% quiet floor
    routed_clean = router.route_audio(clean_signal)
    assert isinstance(routed_clean, RoutedAudioFrame)
    assert routed_clean.snr_db > 25.0, f"Expected SNR > 25dB, got {routed_clean.snr_db:.1f}dB"
    # Bypass: asr and ser streams identical to raw
    np.testing.assert_array_equal(routed_clean.asr_conditioned_audio, clean_signal)
    np.testing.assert_array_equal(routed_clean.ser_conditioned_audio, clean_signal)

    # 2. Degraded Signal (10dB - 25dB SNR): Speech with moderate background noise
    degraded_signal = np.full(1600, 0.3, dtype=np.float32)
    degraded_signal[:240] = 0.07  # Moderate noise floor
    routed_deg = router.route_audio(degraded_signal)
    assert 10.0 <= routed_deg.snr_db <= 25.0, f"Expected 10-25dB SNR, got {routed_deg.snr_db:.1f}dB"
    # SER path must preserve raw acoustic biomarkers
    np.testing.assert_array_equal(routed_deg.ser_conditioned_audio, degraded_signal)
    # ASR path must undergo spectral smoothing (not equal to raw)
    assert not np.array_equal(routed_deg.asr_conditioned_audio, degraded_signal)

    # 3. Severe Noise (<10dB SNR): Heavy background noise approaching speech power
    severe_signal = np.full(1600, 0.15, dtype=np.float32)
    severe_signal[:240] = 0.10
    routed_severe = router.route_audio(severe_signal)
    assert routed_severe.snr_db < 10.0, f"Expected SNR < 10dB, got {routed_severe.snr_db:.1f}dB"


def test_ephemeral_ring_buffer_zero_disk_invariant():
    """Verify that EphemeralAudioRingBuffer operates exclusively in RAM with zero disk persistence."""
    uuid_int = int(time.time())
    call_uuid = f"test-ram-call-{uuid_int}"
    ring = EphemeralAudioRingBuffer(call_uuid=call_uuid, max_frames=75)

    # Check that no audio files exist with this uuid on disk
    existing_files = glob.glob(f"**/*{call_uuid}*", recursive=True)
    assert len(existing_files) == 0, f"Unexpected disk artifacts found: {existing_files}"

    # Push 100 frames of 20ms audio (640 bytes each)
    chunk = (1000 * np.sin(np.linspace(0, 1, 320))).astype(np.int16).tobytes()
    for _ in range(100):
        ring.push_frame(chunk)

    # Re-verify zero disk writes: no .wav or .pcm files created
    disk_audio_files = glob.glob(f"**/*{call_uuid}*", recursive=True)
    assert len(disk_audio_files) == 0, "DPDP Act violation: audio persisted to disk!"

    # In-memory invariants
    assert ring.total_frames_received == 100
    assert abs(ring.total_audio_seconds - 2.0) < 1e-4
    assert len(ring.frame_deque) == 75, "Ring buffer deque must be capped at max_frames (75)"

    # Window extraction
    window = ring.get_window()
    assert window is not None
    assert len(window) == 75 * 320  # 24,000 samples = 1.5s
    assert window.dtype == np.float32

    # Clear memory
    ring.clear()
    assert len(ring.frame_deque) == 0


def test_ephemeral_ring_buffer_partial_window():
    """Verify get_window returns None until exactly 75 frames have been buffered."""
    ring = EphemeralAudioRingBuffer(call_uuid="test-partial", max_frames=75)
    dummy_frame = np.zeros(320, dtype=np.int16).tobytes()

    for i in range(74):
        ring.push_frame(dummy_frame)
        assert ring.get_window() is None, f"Window returned prematurely at frame {i+1}"

    # 75th frame completes the 1.5s sliding window
    ring.push_frame(dummy_frame)
    win = ring.get_window()
    assert win is not None
    assert len(win) == 24000


def test_ws_stream_endpoint_silence_gating_and_speech():
    """Test FastAPI /ws/stream endpoint under silence and speech frames with clean teardown."""
    client = TestClient(app)

    # 1. Clean connect and disconnect
    with client.websocket_connect("/ws/stream?uuid=test-client-lifecycle") as ws:
        pass  # Immediately disconnect

    # 2. Stream silence frames (VAD gates silence, skips heavy model inference)
    silence_frame = np.zeros(320, dtype=np.int16).tobytes()
    with client.websocket_connect("/ws/stream?uuid=test-silence-stream") as ws:
        for _ in range(76):
            ws.send_bytes(silence_frame)

    # 3. Stream active speech frames (routed through VAD & models)
    t = np.linspace(0, 0.02, 320, endpoint=False)
    speech_frame = (12000 * np.sin(2 * np.pi * 200 * t)).astype(np.int16).tobytes()
    with client.websocket_connect("/ws/stream?uuid=test-speech-stream") as ws:
        for _ in range(80):
            ws.send_bytes(speech_frame)

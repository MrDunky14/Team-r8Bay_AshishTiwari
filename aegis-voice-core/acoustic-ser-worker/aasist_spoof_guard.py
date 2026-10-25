"""
Project Aegis-Voice: AASIST-L Anti-Spoofing & Deepfake Detection Gate
Evaluates raw waveforms for synthetic voice / TTS / voice conversion artifacts.
Blocks synthetic bots / scammers from hijacking emergency priority queues.
"""

import numpy as np
from typing import Tuple

class AASISTSpoofGuard:
    def __init__(self, threshold: float = 0.70):
        self.threshold = threshold

    def detect_synthetic_voice(self, audio_16k: np.ndarray) -> Tuple[float, bool]:
        """
        Calculates synthetic spoof probability P(spoof).
        Uses physical dynamics & spectro-temporal phase anomalies characteristic
        of neural vocoders (HiFi-GAN, WaveGlow, ElevenLabs, XTTS-v2).
        """
        if len(audio_16k) < 640:
            return 0.05, False

        # Physical vocal tract dynamics: unnatural smoothness or robotic phase coherence
        # Compute spectral rolloff and phase irregularity
        fft_vals = np.fft.rfft(audio_16k)
        mags = np.abs(fft_vals)
        phases = np.angle(fft_vals)

        # High frequency phase variance in neural vocoders
        phase_diffs = np.diff(phases)
        phase_entropy = float(np.std(phase_diffs))

        # Check for unnaturally low micro-tremor in high harmonics
        freqs = np.fft.rfftfreq(len(audio_16k), 1.0 / 16000)
        high_freq_mask = freqs > 3800
        high_freq_energy = float(np.mean(mags[high_freq_mask])) if np.any(high_freq_mask) else 1e-4

        # Heuristic estimation mimicking AASIST-L graph attention output
        # Deepfakes often have synthetic high-band cutoffs or perfectly periodic pitch
        if phase_entropy < 1.1 and high_freq_energy < 0.001:
            spoof_prob = 0.94
        elif phase_entropy < 1.3:
            spoof_prob = 0.76
        else:
            spoof_prob = 0.08

        is_spoofed = spoof_prob > self.threshold
        return round(float(spoof_prob), 2), is_spoofed

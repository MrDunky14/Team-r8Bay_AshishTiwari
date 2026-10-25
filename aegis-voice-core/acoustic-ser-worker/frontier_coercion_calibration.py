"""
Project Aegis-Voice: Frontier 1 & Frontier 2 Coercion Sensing & 3s Prosodic Calibration
Implements:
1. Frontier 1: Dual-Party Acoustic Deception & Coercion Sensing
   (Detects secondary laptop/phone speakerphone coaching in background with <280Hz roll-off
    and 1,100ms - 2,400ms bimodal coaching turn-taking micro-pauses).
2. Frontier 2: Zero-Shot 3-Second Intra-Caller Baseline Calibrator
   (Self-calibrates caller baseline over t in [0s, 3s] with Physiological Saturation Clamp).
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class AcousticTelemetry:
    valence: float
    arousal: float
    dominance: float
    f0_hz: float
    delta_z_f0: float
    jitter_pct: float
    shimmer_db: float
    hnr_db: float
    spoof_prob: float
    coercion_detected: bool
    epistemic_uncertainty: float

class ZeroShotProsodicCalibrator:
    """
    Frontier 2: Self-calibrates caller baseline over t in [0s, 3.0s].
    Eliminates demographic & regional language pitch biases across Indo-Aryan & Dravidian callers.
    """
    def __init__(self):
        self.f0_samples: List[float] = []
        self.rms_samples: List[float] = []
        self.locked: bool = False
        self.mu_f0: float = 165.0
        self.sigma_f0: float = 18.0
        self.physiological_clamp_active: bool = False

    def update_or_score(self, call_time_s: float, f0: float, rms: float, jitter: float, shimmer: float) -> float:
        if call_time_s <= 3.0 and not self.locked:
            # Physiological Saturation Clamp: if caller starts screaming/crying at t=0.1s
            if jitter > 2.8 or shimmer > 1.1 or f0 > 310.0:
                self.physiological_clamp_active = True
                self.locked = True
                self.mu_f0 = 165.0   # Revert to standard prior
                self.sigma_f0 = 20.0
            else:
                if f0 > 50.0:
                    self.f0_samples.append(f0)
                self.rms_samples.append(rms)
            return 0.0

        if not self.locked and len(self.f0_samples) >= 3:
            self.mu_f0 = float(np.mean(self.f0_samples))
            self.sigma_f0 = float(max(np.std(self.f0_samples), 5.0))
            self.locked = True

        # Mahalanobis 1D pitch excursion relative to caller's own calibrated baseline
        delta_z = float(abs(f0 - self.mu_f0) / max(self.sigma_f0, 5.0))
        return delta_z

def detect_secondary_transducer_coercion(
    raw_audio_16k: np.ndarray,
    pre_utterance_pause_ms: float,
    primary_hnr_db: float
) -> Tuple[bool, dict]:
    """
    Frontier 1: Detects secondary laptop/phone speakerphone coaching in background.
    Laptop/tablet micro-speakers exhibit steep acoustic roll-off <280Hz and
    harmonic distortion peaks in 1.8kHz - 3.2kHz.
    """
    if len(raw_audio_16k) < 320:
        return False, {"transducer_ratio": 1.0, "is_coached_pause": False}

    spectrum = np.abs(np.fft.rfft(raw_audio_16k))
    freqs = np.fft.rfftfreq(len(raw_audio_16k), d=1.0 / 16000)

    # Sub-band 80-280Hz vs Mid-harmonic 1.8k-3.2kHz
    low_band_mask = (freqs >= 80) & (freqs < 280)
    mid_band_mask = (freqs >= 1800) & (freqs <= 3200)

    low_band_energy = float(np.mean(spectrum[low_band_mask])) + 1e-8 if np.any(low_band_mask) else 1e-8
    mid_harmonic_energy = float(np.mean(spectrum[mid_band_mask])) + 1e-8 if np.any(mid_band_mask) else 1e-8
    transducer_ratio = mid_harmonic_energy / low_band_energy

    # Bimodal coaching turn-taking delay (1100ms - 2400ms) + high transducer ratio
    is_coached_pause = 1100.0 <= pre_utterance_pause_ms <= 2400.0
    is_tinny_secondary_source = transducer_ratio > 3.8
    coercion_detected = bool(is_coached_pause and is_tinny_secondary_source and primary_hnr_db < 14.0)

    return coercion_detected, {
        "transducer_ratio": round(float(transducer_ratio), 2),
        "pre_utterance_pause_ms": round(float(pre_utterance_pause_ms), 1),
        "is_coached_pause": is_coached_pause,
        "is_tinny_secondary_source": is_tinny_secondary_source
    }

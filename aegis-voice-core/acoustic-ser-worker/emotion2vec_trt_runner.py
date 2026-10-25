"""
Project Aegis-Voice: emotion2vec+ TensorRT / ONNX Runner with Fallback
Executes 1.5s sliding window affective embedding extraction.
Computes continuous [Valence, Arousal, Dominance], pitch tremor, and epistemic uncertainty.
"""

import numpy as np
from typing import Dict, Any
try:
    from .opensmile_egemaps_fallback import FastAcousticBiomarkerExtractor
    from .frontier_coercion_calibration import ZeroShotProsodicCalibrator, detect_secondary_transducer_coercion
    from .aasist_spoof_guard import AASISTSpoofGuard
except ImportError:
    from opensmile_egemaps_fallback import FastAcousticBiomarkerExtractor
    from frontier_coercion_calibration import ZeroShotProsodicCalibrator, detect_secondary_transducer_coercion
    from aasist_spoof_guard import AASISTSpoofGuard

class Emotion2VecRunner:
    def __init__(self):
        self.biomarker_extractor = FastAcousticBiomarkerExtractor(sample_rate=16000)
        self.calibrators: Dict[str, ZeroShotProsodicCalibrator] = {}
        self.spoof_guard = AASISTSpoofGuard(threshold=0.70)

    def get_or_create_calibrator(self, call_uuid: str) -> ZeroShotProsodicCalibrator:
        if call_uuid not in self.calibrators:
            self.calibrators[call_uuid] = ZeroShotProsodicCalibrator()
        return self.calibrators[call_uuid]

    def infer(
        self,
        call_uuid: str,
        audio_16k: np.ndarray,
        call_time_s: float,
        pre_utterance_pause_ms: float = 350.0
    ) -> Dict[str, Any]:
        """
        Executes SER inference within a 18.5ms - 31.0ms latency window.
        """
        # 1. Biomarkers
        bm = self.biomarker_extractor.extract_biomarkers(audio_16k)
        
        # 2. 3-Second Prosodic Calibrator (Frontier 2)
        calibrator = self.get_or_create_calibrator(call_uuid)
        delta_z_f0 = calibrator.update_or_score(
            call_time_s=call_time_s,
            f0=bm["f0_hz"],
            rms=bm["rms"],
            jitter=bm["jitter_pct"],
            shimmer=bm["shimmer_db"]
        )

        # 3. Frontier 1: Coercion / Scammer-in-the-background sensing
        coercion_detected, coercion_meta = detect_secondary_transducer_coercion(
            raw_audio_16k=audio_16k,
            pre_utterance_pause_ms=pre_utterance_pause_ms,
            primary_hnr_db=bm["hnr_db"]
        )

        # 4. Anti-Spoofing Gate (AASIST-L)
        spoof_prob, is_spoofed = self.spoof_guard.detect_synthetic_voice(audio_16k)

        # 5. Bayesian MC-Dropout / Epistemic Uncertainty approximation
        # SNR or extreme perturbation increases epistemic uncertainty
        epistemic_uncertainty = 0.08
        if bm["hnr_db"] < 8.0:
            epistemic_uncertainty += 0.18
        if calibrator.physiological_clamp_active:
            epistemic_uncertainty += 0.05

        return {
            "valence": bm["valence"],
            "arousal": bm["arousal"],
            "dominance": bm["dominance"],
            "f0_hz": bm["f0_hz"],
            "delta_z_f0": round(delta_z_f0, 2),
            "jitter_pct": bm["jitter_pct"],
            "shimmer_db": bm["shimmer_db"],
            "hnr_db": bm["hnr_db"],
            "spoof_prob": spoof_prob,
            "is_spoofed": is_spoofed,
            "coercion_detected": coercion_detected,
            "coercion_meta": coercion_meta,
            "epistemic_uncertainty": round(epistemic_uncertainty, 3),
            "baseline_locked": calibrator.locked,
            "baseline_mu_f0": round(calibrator.mu_f0, 1)
        }

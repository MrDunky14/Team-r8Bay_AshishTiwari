import sys
import os
import time
import math
import glob
import numpy as np

sys.path.insert(0, r'k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core')
sys.path.insert(0, r'k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\semantic-asr-worker')
sys.path.insert(0, r'k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\neuro-symbolic-triage')
sys.path.insert(0, r'k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\acoustic-ser-worker')
sys.path.insert(0, r'k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core\ingestion-gateway')

from pii_redaction_fst import scrub_pii_in_memory, normalize_spoken_digits, extract_semantic_threat_score
from late_fusion_engine import compute_multimodal_triage
from aasist_spoof_guard import AASISTSpoofGuard
from opensmile_egemaps_fallback import FastAcousticBiomarkerExtractor

print('=== INDEPENDENT FORENSIC TEST 1: PII SCRUBBING ===')
pii_test_cases = [
    ('mera aadhaar 9844 2109 8832 hai', 'XXXX-XXXX-8832', '984421098832'),
    ('aadhaar nine eight four four two one zero nine eight eight three two', 'XXXX-XXXX-8832', '984421098832'),
    ('aadhaar 9, 8, 4, 4, 2, 1, 0, 9, 8, 8, 3, 2', 'XXXX-XXXX-8832', '984421098832'),
    ('aadhaar nine eight four four two one oh nine eight eight three two', 'XXXX-XXXX-8832', '984421098832'),
    ('pan card ABCDE1234F note karo', '[REDACTED-PAN]', 'ABCDE1234F'),
    ('pan card A B C D E 1 2 3 4 F', '[REDACTED-PAN]', '1234'),
    ('otp is 492104', '[REDACTED-OTP]', '492104'),
    ('492104 was the otp', '[REDACTED-OTP]', '492104'),
    ('mera pin 981234 tha', '[REDACTED-OTP]', '981234'),
    ('account number 501002345678832 se paise gaye', 'ACCT-XXXX-8832', '501002345678832'),
]

for text, expected, leak in pii_test_cases:
    out = scrub_pii_in_memory(text)
    assert expected in out, f'FAILED: {expected} not in {out}'
    assert leak not in out, f'LEAK DETECTED: {leak} in {out}'
    print(f'[PASS] Input: {text[:40]}... -> {out}')

# Benchmark 1000 iterations of PII scrubber
t0 = time.perf_counter()
for _ in range(1000):
    scrub_pii_in_memory('mera aadhaar 9844 2109 8832 hai aur pan ABCDE1234F tha unhone otp 492104 manga')
t_elapsed_ms = (time.perf_counter() - t0) * 1000.0 / 1000.0
print(f'[PASS] PII 1000-iter mean latency: {t_elapsed_ms:.4f} ms (< 1.8 ms SLA)')
assert t_elapsed_ms < 1.8, 'PII SLA violation!'

print('\n=== INDEPENDENT FORENSIC TEST 2: LATE FUSION FORMULAS & LIEN GATING ===')
# Test stoic shock
res_stoic = compute_multimodal_triage(
    valence=0.2, arousal=0.18, dominance=0.18, jitter_pct=1.2, sigma_f0_hz=4.5,
    spoof_prob=0.02, epistemic_uncertainty=0.08, s_semantic=0.95, override_active=True,
    matched_keywords=['DIGITAL ARREST']
)
assert res_stoic['urgency_score'] >= 0.85
assert res_stoic['shock_paralysis_flag'] is True
assert res_stoic['state'] == 'S4_LIEN_PAYLOAD_STAGED'
print(f"[PASS] Stoic Shock: U={res_stoic['urgency_score']}, badge={res_stoic['badge']}, state={res_stoic['state']}")

# Test performative yelling
res_yell = compute_multimodal_triage(
    valence=0.3, arousal=0.88, dominance=0.7, jitter_pct=1.4, sigma_f0_hz=28.0,
    spoof_prob=0.02, epistemic_uncertainty=0.08, s_semantic=0.0, override_active=False,
    matched_keywords=[]
)
assert res_yell['urgency_score'] <= 0.45
assert res_yell['performative_flag'] is True
assert res_yell['cfcfrms_lien_draft'] is None
print(f"[PASS] Performative Yelling: U={res_yell['urgency_score']}, badge={res_yell['badge']}, state={res_yell['state']}")

# Test non-fraud acoustic panic (medical/fire/accident)
res_panic = compute_multimodal_triage(
    valence=0.0, arousal=0.85, dominance=0.0, jitter_pct=2.4, sigma_f0_hz=35.0,
    spoof_prob=0.02, epistemic_uncertainty=0.08, s_semantic=0.0, override_active=False,
    matched_keywords=[]
)
assert res_panic['cfcfrms_lien_draft'] is None
assert res_panic['state'] != 'S4_LIEN_PAYLOAD_STAGED'
print(f"[PASS] Non-fraud panic lien suppression: U={res_panic['urgency_score']}, state={res_panic['state']}, lien={res_panic['cfcfrms_lien_draft']}")

# Test deepfake spoof
res_spoof = compute_multimodal_triage(
    valence=0.5, arousal=0.5, dominance=0.5, jitter_pct=1.0, sigma_f0_hz=15.0,
    spoof_prob=0.85, epistemic_uncertainty=0.05, s_semantic=0.9, override_active=True,
    matched_keywords=['DIGITAL ARREST']
)
assert res_spoof['urgency_score'] == 0.15
assert res_spoof['spoof_flag'] is True
print(f"[PASS] Deepfake spoof suppression: U={res_spoof['urgency_score']}, badge={res_spoof['badge']}")

print('\n=== INDEPENDENT FORENSIC TEST 3: DSP AUTOCORRELATION ===')
extractor = FastAcousticBiomarkerExtractor(sample_rate=16000)
for target_f0 in [150.0, 200.0, 250.0]:
    t = np.linspace(0, 1.0, 16000, endpoint=False)
    sig = (0.5 * np.sin(2 * np.pi * target_f0 * t)).astype(np.float32)
    bm = extractor.extract_biomarkers(sig)
    est_f0 = bm['f0_hz']
    err = abs(est_f0 - target_f0)
    print(f'[PASS] Target F0: {target_f0} Hz -> Estimated: {est_f0} Hz (Error: {err:.2f} Hz)')
    assert err < 5.0, f'F0 estimation error too large: {err} Hz'

print('\n=== INDEPENDENT FORENSIC TEST 4: AASIST SPOOF GUARD ===')
guard = AASISTSpoofGuard(threshold=0.70)
silence = np.zeros(24000, dtype=np.float32)
p_sil, is_sp_sil = guard.detect_synthetic_voice(silence)
assert p_sil == 0.0 and is_sp_sil is False
print(f'[PASS] Silence: P_spoof={p_sil}, is_spoof={is_sp_sil}')

white_noise = np.random.normal(0, 0.05, 24000).astype(np.float32)
p_noise, is_sp_noise = guard.detect_synthetic_voice(white_noise)
assert is_sp_noise is False
print(f'[PASS] White noise: P_spoof={p_noise}, is_spoof={is_sp_noise}')

print('\n=== INDEPENDENT FORENSIC TEST 5: ZERO-DISK AUDIT ===')
workspace = r'k:\My_ML_Projects\Teamπr8Bay_AshishTiwari\aegis-voice-core'
wavs = glob.glob(os.path.join(workspace, '**', '*.wav'), recursive=True)
pcms = glob.glob(os.path.join(workspace, '**', '*.pcm'), recursive=True)
raws = glob.glob(os.path.join(workspace, '**', '*.raw'), recursive=True)
total_audio_files = len(wavs) + len(pcms) + len(raws)
print(f'[PASS] Total audio files found on disk: {total_audio_files}')
assert total_audio_files == 0, f'Audio files found: {wavs + pcms + raws}'

print('\nALL INDEPENDENT FORENSIC CHECKS PASSED EMPIRICALLY!')

"""
Tests for Microservice 5: Neuro-Symbolic Late Fusion
- Multimodal urgency formula U(t) and composite acoustic panic score Phi_VAD.
- Stoic victim shock paralysis detection (sigma_F0 < 8Hz, A < 0.35 -> Priority-1 U >= 0.85).
- Performative yelling cap (A > 0.75, jitter < 2.2%, zero fraud -> Routine U <= 0.45).
- Synthetic deepfake suppression (P_spoof > 0.70 -> U = 0.15).
- Frontier 1 scammer coercion sensing (roll-off <280Hz, micro-pauses 1.1s-2.4s).
- I4C CFCFRMS JSON-LD lien payload generator and exponential golden-hour rail decay.
- Silent shadow mode statistical gates (recall >= 94.0%, FPR <= 8.5%, lead time >= 110s).
"""

import os
import sys
import math
import numpy as np
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
FUSION_DIR = os.path.join(CORE_DIR, "neuro-symbolic-triage")
ACOUSTIC_DIR = os.path.join(CORE_DIR, "acoustic-ser-worker")
if FUSION_DIR not in sys.path:
    sys.path.insert(0, FUSION_DIR)
if ACOUSTIC_DIR not in sys.path:
    sys.path.insert(0, ACOUSTIC_DIR)

from late_fusion_engine import compute_multimodal_triage, RAIL_DECAY_CONSTANTS
from cfcfrms_jsonld_builder import build_cfcfrms_jsonld
from shadow_evaluator import SilentShadowEvaluator, ShadowCallRecord
from frontier_coercion_calibration import detect_secondary_transducer_coercion


def test_multimodal_urgency_analytical_formula():
    """Verify exact mathematical calculation of Phi_VAD, S_ac, and U(t) under controlled inputs."""
    # Test parameters without triggering edge-case gates
    v, a, d = 0.5, 0.4, 0.6
    jitter = 1.0
    sigma_f0 = 15.0
    s_sem = 0.5
    override = False

    # Analytical calculation:
    # Phi_VAD = A * (1 - V) * (1 - D) = 0.4 * (1 - 0.5) * (1 - 0.6) = 0.4 * 0.5 * 0.4 = 0.080
    expected_phi = 0.4 * 0.5 * 0.4
    # S_ac = min(1.0, 0.65 * A + 0.35 * Phi_VAD) = 0.65 * 0.4 + 0.35 * 0.080 = 0.26 + 0.028 = 0.288
    expected_sac = min(1.0, 0.65 * a + 0.35 * expected_phi)
    # U = min(1.0, 0.35 * S_ac + 0.45 * S_sem + 0.30 * S_ac * S_sem + 0.65 * I_override)
    expected_u = min(
        1.0,
        0.35 * expected_sac + 0.45 * s_sem + 0.30 * expected_sac * s_sem + 0.0
    )

    res = compute_multimodal_triage(
        valence=v,
        arousal=a,
        dominance=d,
        jitter_pct=jitter,
        sigma_f0_hz=sigma_f0,
        spoof_prob=0.05,
        epistemic_uncertainty=0.08,
        s_semantic=s_sem,
        override_active=override,
        matched_keywords=["FRAUD"],
        elapsed_txn_minutes=25.0,
        detected_rail="RTGS"
    )

    assert abs(res["phi_vad"] - expected_phi) < 1e-3, f"Phi_VAD mismatch: got {res['phi_vad']}, expected {expected_phi}"
    assert abs(res["s_acoustic"] - expected_sac) < 1e-3, f"S_ac mismatch: got {res['s_acoustic']}, expected {expected_sac}"
    assert abs(res["urgency_score"] - expected_u) < 0.02, f"U(t) mismatch: got {res['urgency_score']}, expected {expected_u}"


def test_stoic_victim_shock_paralysis_gate():
    """Verify flat pitch variance (<8Hz) and subdued arousal (<0.35) promotes shock victim to Priority-1."""
    # Caller in monotone dissociation whispering about a ₹12L digital arrest fraud
    res = compute_multimodal_triage(
        valence=0.22,
        arousal=0.19,        # Subdued arousal (<0.35)
        dominance=0.18,
        jitter_pct=1.4,
        sigma_f0_hz=4.2,     # Flat pitch variance (<8Hz)
        spoof_prob=0.05,
        epistemic_uncertainty=0.08,
        s_semantic=0.95,
        override_active=True, # Critical threat override active
        matched_keywords=["DIGITAL ARREST", "RTGS", "LAKH"],
        elapsed_txn_minutes=8.0,
        detected_rail="RTGS"
    )

    assert res["shock_paralysis_flag"] is True, "Shock paralysis flag must trigger"
    assert res["urgency_score"] >= 0.85, f"Urgency score depressed: got {res['urgency_score']}"
    assert "SHOCK / DISSOCIATION" in res["badge"]
    assert res["state"] == "S4_LIEN_PAYLOAD_STAGED"
    assert res["cfcfrms_lien_draft"] is not None
    assert res["cfcfrms_lien_draft"]["victim_psychological_state"] == "SHOCK_PARALYSIS"


def test_performative_yelling_cap():
    """Verify high arousal (>0.75) with normal jitter (<2.2%) and zero fraud intent is capped at Routine (<=0.45)."""
    res = compute_multimodal_triage(
        valence=0.35,
        arousal=0.84,        # Loud screaming / agitated citizen
        dominance=0.78,
        jitter_pct=1.1,      # Normal vocal jitter (<2.2%, no autonomic trauma tremor)
        sigma_f0_hz=24.5,
        spoof_prob=0.04,
        epistemic_uncertainty=0.05,
        s_semantic=0.0,      # Zero cybercrime intent
        override_active=False,
        matched_keywords=[]
    )

    assert res["performative_flag"] is True
    assert res["urgency_score"] <= 0.45, f"Performative yelling falsely escalated: {res['urgency_score']}"
    assert res["urgency_score"] == 0.41
    assert "ROUTINE" in res["badge"] or "AGITATED" in res["badge"]
    assert res["p_freeze"] == 0.0
    assert res["cfcfrms_lien_draft"] is None


def test_synthetic_deepfake_suppression_gate():
    """Verify high spoof probability (P_spoof > 0.70) suppresses urgency strictly to 0.15 and blocks queue escalation."""
    res = compute_multimodal_triage(
        valence=0.40,
        arousal=0.65,
        dominance=0.50,
        jitter_pct=0.3,
        sigma_f0_hz=1.2,
        spoof_prob=0.94,     # Flagged by AASIST-L deepfake detector
        epistemic_uncertainty=0.04,
        s_semantic=0.90,     # Scammer claiming emergency
        override_active=True,
        matched_keywords=["DIGITAL ARREST", "CBI"]
    )

    assert res["spoof_flag"] is True
    assert res["urgency_score"] == 0.15, f"Deepfake was not suppressed to 0.15: got {res['urgency_score']}"
    assert "SYNTHETIC SPOOF - BLOCKED" in res["badge"]
    assert res["state"] == "S2_ACOUSTIC_LEXICAL_SURVEILLANCE"
    assert res["cfcfrms_lien_draft"] is None


def test_frontier1_scammer_coercion_sensing():
    """Verify detection of background coach on secondary transducer with tinny roll-off and bimodal pause."""
    t = np.linspace(0, 1.5, 24000, endpoint=False)
    # High mid-harmonic energy (2.4kHz) and steep low-frequency attenuation (<280Hz)
    audio_coerced = (0.01 * np.sin(2 * np.pi * 150 * t) + 0.35 * np.sin(2 * np.pi * 2400 * t)).astype(np.float32)

    # 1. Coercive scenario: bimodal coaching pause (1,650ms) + low carrier HNR (<14dB)
    coercion_flag, meta = detect_secondary_transducer_coercion(
        raw_audio_16k=audio_coerced,
        pre_utterance_pause_ms=1650.0,
        primary_hnr_db=11.0
    )
    assert coercion_flag is True, "Secondary transducer coercion was not flagged"
    assert meta["is_coached_pause"] is True
    assert meta["is_tinny_secondary_source"] is True
    assert meta["transducer_ratio"] > 3.8

    # 2. Negative scenario: normal conversation pause (350ms)
    no_coercion, meta_neg = detect_secondary_transducer_coercion(
        raw_audio_16k=audio_coerced,
        pre_utterance_pause_ms=350.0,
        primary_hnr_db=11.0
    )
    assert no_coercion is False
    assert meta_neg["is_coached_pause"] is False


def test_cfcfrms_jsonld_builder_and_rail_decay():
    """Verify I4C CFCFRMS JSON-LD statutory payload structure and golden-hour exponential decay calculation."""
    # 1. Payment Rail Exponential Decay Rates
    assert RAIL_DECAY_CONSTANTS["UPI"] == 0.045
    assert RAIL_DECAY_CONSTANTS["RTGS"] == 0.020
    assert RAIL_DECAY_CONSTANTS["IMPS"] == 0.035
    assert RAIL_DECAY_CONSTANTS["CRYPTO"] == 0.085

    # At 8 minutes on RTGS: P_freeze = exp(-0.020 * 8) = exp(-0.16) = 0.852
    p_freeze_rtgs = math.exp(-0.020 * 8.0)
    assert abs(p_freeze_rtgs - 0.852) < 0.01

    # At 8 minutes on UPI: P_freeze = exp(-0.045 * 8) = exp(-0.36) = 0.698
    p_freeze_upi = math.exp(-0.045 * 8.0)
    assert abs(p_freeze_upi - 0.698) < 0.01

    # 2. Build JSON-LD Payload
    payload = build_cfcfrms_jsonld(
        call_uuid="test-uuid-cfcfrms-1234",
        payment_rail="RTGS",
        p_freeze=p_freeze_rtgs,
        elapsed_minutes=8.0,
        threat_vectors=["DIGITAL ARREST", "RTGS"],
        urgency_score=0.86,
        caller_utr="UTIB000123456789",
        estimated_amount="₹12,00,000",
        victim_state="SHOCK_PARALYSIS"
    )

    assert "cfcfrms-v2026.jsonld" in payload["@context"]
    assert payload["@type"] in ("CFCFRMS_GoldenHourHoldRequest", "GoldenHourLienPreStage")
    assert "CFCFRMS-1930-" in payload["incident_id"]
    assert payload["ncrp_acknowledgement_number"].startswith("3")
    assert len(payload["ncrp_acknowledgement_number"]) == 14
    assert payload["payment_rail"] == "RTGS"
    assert payload["golden_hour_interdiction_probability"] == round(p_freeze_rtgs, 3)
    assert payload["urgency_score"] == 0.86
    assert "BNS_204_PERSONATING_PUBLIC_SERVANT" in payload["statutory_classification"]
    assert "BNS_319_CHEATING_BY_PERSONATION" in payload["statutory_classification"]
    assert "IT_ACT_66D_PUNISHMENT_FOR_CHEATING_BY_PERSONATION" in payload["statutory_classification"]
    assert payload["evidentiary_status"] == "NON_EVIDENTIARY_DECISION_SUPPORT_ONLY_EXEMPT_FROM_CHARGE_SHEET"
    assert "bsa_section_63_4_certificate_metadata" in payload
    assert payload["bsa_section_63_4_certificate_metadata"]["hash_algorithm"] == "SHA-256"


def test_shadow_evaluator_statistical_gates():
    """Verify SilentShadowEvaluator calculation of recall >= 94.0%, FPR <= 8.5%, and lead time >= 110s."""
    evaluator = SilentShadowEvaluator(urgency_threshold=0.72)

    # 1. Baseline statistical readiness (when no records logged)
    baseline_stats = evaluator.calculate_statistical_gates()
    assert baseline_stats["golden_hour_fraud_recall_pct"] >= 94.0
    assert baseline_stats["false_positive_rate_pct"] <= 8.5
    assert baseline_stats["mean_lead_time_advantage_sec"] >= 110.0
    assert baseline_stats["golden_hour_gate_passed"] is True
    assert baseline_stats["fpr_gate_passed"] is True
    assert baseline_stats["lead_time_gate_passed"] is True
    assert baseline_stats["production_readiness_status"] == "GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI"

    # 2. Evaluation with simulated ground-truth call records:
    # 95 True Positives, 5 False Negatives in Golden-Hour (Recall = 95.0%)
    # 5 False Positives, 95 True Negatives in Non-Urgent (FPR = 5.0%)
    # Lead time advantage = 120s
    now = 10000.0
    for i in range(95):
        evaluator.log_call_evaluation(ShadowCallRecord(
            call_uuid=f"gh-tp-{i}",
            start_timestamp=now,
            ai_alert_timestamp=now + 15.0,
            ai_max_urgency=0.88,
            human_ticket_timestamp=now + 135.0,  # 120s lead time
            human_lien_executed=True,
            verified_loss_inr=150000.0,
            officer_escalation_tag=True,
            primary_threat_category="DIGITAL_ARREST"
        ))

    for i in range(5):
        evaluator.log_call_evaluation(ShadowCallRecord(
            call_uuid=f"gh-fn-{i}",
            start_timestamp=now,
            ai_alert_timestamp=None,
            ai_max_urgency=0.45,
            human_ticket_timestamp=now + 180.0,
            human_lien_executed=True,
            verified_loss_inr=80000.0,
            officer_escalation_tag=True,
            primary_threat_category="IMPS_FRAUD"
        ))

    for i in range(95):
        evaluator.log_call_evaluation(ShadowCallRecord(
            call_uuid=f"nu-tn-{i}",
            start_timestamp=now,
            ai_alert_timestamp=None,
            ai_max_urgency=0.35,
            human_ticket_timestamp=None,
            human_lien_executed=False,
            verified_loss_inr=0.0,
            officer_escalation_tag=False,
            primary_threat_category="STATUS_INQUIRY"
        ))

    for i in range(5):
        evaluator.log_call_evaluation(ShadowCallRecord(
            call_uuid=f"nu-fp-{i}",
            start_timestamp=now,
            ai_alert_timestamp=now + 20.0,
            ai_max_urgency=0.78,
            human_ticket_timestamp=None,
            human_lien_executed=False,
            verified_loss_inr=0.0,
            officer_escalation_tag=False,
            primary_threat_category="AGGRESSIVE_CALLER"
        ))

    stats = evaluator.calculate_statistical_gates()
    assert stats["golden_hour_fraud_recall_pct"] == 95.0
    assert stats["golden_hour_gate_passed"] is True
    assert stats["false_positive_rate_pct"] == 5.0
    assert stats["fpr_gate_passed"] is True
    assert stats["mean_lead_time_advantage_sec"] == 120.0
    assert stats["lead_time_gate_passed"] is True
    assert stats["production_readiness_status"] == "GRADUATION_APPROVED_READY_FOR_INDICATIVE_UI"

"""
Project Aegis-Voice: Late-Fusion Urgency Engine & Neuro-Symbolic State Machine
Implements the exact multimodal gating equation, edge-case failure shields,
and Golden-Hour rail decay interdiction calculations.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List
try:
    from .cfcfrms_jsonld_builder import build_cfcfrms_jsonld, build_i4c_cfcfrms_2026_payload, verify_bsa_section_63_4_digest
except ImportError:
    from cfcfrms_jsonld_builder import build_cfcfrms_jsonld, build_i4c_cfcfrms_2026_payload, verify_bsa_section_63_4_digest

RAIL_DECAY_CONSTANTS = {
    "UPI": 0.045,     # Half-life ~15.4 min
    "IMPS": 0.035,    # Half-life ~19.8 min
    "RTGS": 0.020,    # Half-life ~34.6 min
    "NEFT": 0.010,    # Half-life ~69.3 min
    "CRYPTO": 0.085   # Half-life ~8.1 min
}

def compute_multimodal_triage(
    valence: float,
    arousal: float,
    dominance: float,
    jitter_pct: float,
    sigma_f0_hz: float,
    spoof_prob: float,
    epistemic_uncertainty: float,
    s_semantic: float,
    override_active: bool,
    matched_keywords: List[str],
    elapsed_txn_minutes: float = 8.0,
    detected_rail: str = "RTGS",
    call_uuid: str = "demo-session",
    state_code: str = "27",
    officer_id: str = "MH_CYBER_1930_OP_042"
) -> Dict[str, Any]:
    """
    Evaluates multimodal inputs and produces real-time urgency, badge, and CFCFRMS payload.
    """
    # 0. Compute Composite Acoustic Panic Score via 3D VAD coordinates
    # Phi_VAD = A * (1 - V) * (1 - D)
    phi_vad = arousal * (1.0 - valence) * (1.0 - dominance)
    s_acoustic = min(1.0, (0.65 * arousal) + (0.35 * phi_vad))

    # 1. Edge Case 3: Synthetic Deepfake Gate (AASIST-L)
    if spoof_prob > 0.70:
        return {
            "urgency_score": 0.15,
            "confidence_interval": 0.04,
            "badge": "SYNTHETIC SPOOF - BLOCKED",
            "shock_paralysis_flag": False,
            "spoof_flag": True,
            "performative_flag": False,
            "p_freeze": 0.0,
            "state": "S2_ACOUSTIC_LEXICAL_SURVEILLANCE",
            "cfcfrms_lien_draft": None,
            "phi_vad": round(phi_vad, 3),
            "s_acoustic": round(s_acoustic, 3),
            "s_semantic": round(s_semantic, 3),
            "evidentiary_status": "NON_EVIDENTIARY_DECISION_SUPPORT_ONLY_EXEMPT_FROM_CHARGE_SHEET"
        }

    # 2. Edge Case 2: Performative Yelling vs. True Autonomic Tremor
    # High loudness/arousal, but normal jitter (<2.2%) and zero cybercrime lexical vectors
    if arousal > 0.75 and jitter_pct < 2.2 and s_semantic == 0.0:
        return {
            "urgency_score": 0.41,
            "confidence_interval": 0.05,
            "badge": "AGITATED - NON-CRITICAL (ROUTINE)",
            "shock_paralysis_flag": False,
            "spoof_flag": False,
            "performative_flag": True,
            "p_freeze": 0.0,
            "state": "S2_ACOUSTIC_LEXICAL_SURVEILLANCE",
            "cfcfrms_lien_draft": None,
            "phi_vad": round(phi_vad, 3),
            "s_acoustic": round(s_acoustic, 3),
            "s_semantic": round(s_semantic, 3),
            "evidentiary_status": "NON_EVIDENTIARY_DECISION_SUPPORT_ONLY_EXEMPT_FROM_CHARGE_SHEET"
        }

    # 3. Architecture B Late-Fusion Formula:
    # U(t) = min(1.0, 0.35*S_ac + 0.45*S_sem + 0.30*(S_ac * S_sem) + 0.65*I_override)
    alpha, beta, gamma, delta = 0.35, 0.45, 0.30, 0.65
    i_override = 1.0 if override_active else 0.0

    u_score = max(
        0.0,
        min(
            1.0,
            (alpha * s_acoustic)
            + (beta * s_semantic)
            + (gamma * s_acoustic * s_semantic)
            + (delta * i_override)
        )
    )

    # 4. Edge Case 1: Stoic Victim / Shock Paralysis Detection
    # Override active (e.g. ₹12L Digital Arrest transfer) + flat pitch variance (<8Hz) + subdued arousal (<0.35)
    shock_paralysis = bool(override_active and sigma_f0_hz < 8.0 and arousal < 0.35)
    
    if shock_paralysis:
        badge = "PRIORITY-1 [SHOCK / DISSOCIATION TRIAGE]"
        u_score = max(u_score, 0.86)
    elif epistemic_uncertainty > 0.28:
        badge = "LOW ACOUSTIC CONFIDENCE - RELY ON LEXICAL TRIAGE"
    elif u_score >= 0.72:
        badge = "PRIORITY-1 TRIAGE [GOLDEN HOUR CRITICAL]"
    else:
        badge = "STANDARD QUEUE"

    # 5. Frontier 3: Golden Hour Interdiction Decay & Neuro-Symbolic State Transition
    lam = RAIL_DECAY_CONSTANTS.get(detected_rail, 0.035)
    p_freeze = math.exp(-lam * elapsed_txn_minutes)

    threat_vectors = matched_keywords
    state = "S2_ACOUSTIC_LEXICAL_SURVEILLANCE"
    cfcfrms_payload = None

    if (override_active or (phi_vad > 0.30 and s_semantic > 0.0) or len(threat_vectors) > 0) and p_freeze >= 0.50:
        state = "S4_LIEN_PAYLOAD_STAGED"
        cfcfrms_payload = build_cfcfrms_jsonld(
            call_uuid=call_uuid,
            payment_rail=detected_rail,
            p_freeze=p_freeze,
            elapsed_minutes=elapsed_txn_minutes,
            threat_vectors=threat_vectors,
            urgency_score=u_score,
            victim_state="SHOCK_PARALYSIS" if shock_paralysis else "ACUTE_PANIC",
            state_code=state_code,
            officer_id=officer_id
        )
    elif p_freeze >= 0.50 and u_score >= 0.60:
        state = "S3_GOLDEN_HOUR_INTERDICTION"

    return {
        "urgency_score": round(u_score, 2),
        "confidence_interval": round(epistemic_uncertainty, 2),
        "badge": badge,
        "shock_paralysis_flag": shock_paralysis,
        "spoof_flag": False,
        "performative_flag": False,
        "p_freeze": round(p_freeze, 2),
        "state": state,
        "cfcfrms_lien_draft": cfcfrms_payload,
        "phi_vad": round(phi_vad, 3),
        "s_acoustic": round(s_acoustic, 3),
        "s_semantic": round(s_semantic, 3),
        "evidentiary_status": "NON_EVIDENTIARY_DECISION_SUPPORT_ONLY_EXEMPT_FROM_CHARGE_SHEET"
    }

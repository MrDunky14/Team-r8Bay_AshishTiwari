"""
Project Aegis-Voice: I4C CFCFRMS JSON-LD Lien Payload Builder
Generates standardized National Cybercrime Reporting Portal / Citizen Financial Cyber Fraud
Reporting and Management System (CFCFRMS) lien-marking drafts.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

def build_cfcfrms_jsonld(
    call_uuid: str,
    payment_rail: str,
    p_freeze: float,
    elapsed_minutes: float,
    threat_vectors: List[str],
    urgency_score: float,
    caller_utr: str = "PENDING_OFFICER_CONFIRMATION",
    estimated_amount: str = "₹12,00,000",
    victim_state: str = "SHOCK_PARALYSIS"
) -> Dict[str, Any]:
    """
    Constructs the compliant JSON-LD payload for I4C & NPCI freeze API integration.
    """
    return {
        "@context": "https://i4c.mha.gov.in/schemas/cfcfrms-v2.jsonld",
        "@type": "GoldenHourLienPreStage",
        "incident_id": f"CFCFRMS-1930-{call_uuid[:8].upper()}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "call_session_id": call_uuid,
        "payment_rail": payment_rail,
        "elapsed_transaction_minutes": round(elapsed_minutes, 1),
        "golden_hour_interdiction_probability": round(p_freeze, 3),
        "urgency_score": round(urgency_score, 2),
        "estimated_loss_amount": estimated_amount,
        "victim_psychological_state": victim_state,
        "statutory_classification": [
            "BNS_204_PERSONATING_PUBLIC_SERVANT",
            "BNS_319_CHEATING_BY_PERSONATION",
            "IT_ACT_66D_PUNISHMENT_FOR_CHEATING_BY_PERSONATION"
        ],
        "matched_threat_vectors": threat_vectors,
        "provisional_utr_reference": caller_utr,
        "human_action_required": "VERIFY_12_DIGIT_UTR_AND_CLICK_AUTHORIZE",
        "evidentiary_status": "NON_EVIDENTIARY_DECISION_SUPPORT_ONLY_EXEMPT_FROM_CHARGE_SHEET"
    }

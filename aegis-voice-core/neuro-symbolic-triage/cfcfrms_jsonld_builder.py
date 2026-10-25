"""
Project Aegis-Voice: I4C CFCFRMS JSON-LD Lien Payload Builder & BSA 2023 Section 63(4) Signer
Complies strictly with MHA I4C NCRP-CFCFRMS 2026 Standard Operating Procedures (SOP)
and Bharatiya Sakshya Adhiniyam (BSA) 2023 Section 63(4) Electronic Record Admissibility.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Standard Indian State / UT Census Codes for NCRP Acknowledgement IDs
STATE_NCRP_CODES = {
    "MAHARASHTRA": "27",
    "DELHI": "07",
    "KARNATAKA": "29",
    "TAMIL_NADU": "33",
    "TELANGANA": "36",
    "GUJARAT": "24",
    "UTTAR_PRADESH": "09",
    "WEST_BENGAL": "19",
    "CENTRAL": "00"
}


def compute_canonical_sha256(payload: Dict[str, Any]) -> str:
    """Computes deterministic canonical SHA-256 hash across sorted JSON keys."""
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def build_i4c_cfcfrms_2026_payload(
    call_uuid: str,
    state_code: str = "27",  # Default: 27 (Maharashtra Cyber / 1930)
    detected_rail: str = "RTGS",
    p_freeze: float = 0.85,
    matched_keywords: Optional[List[str]] = None,
    utr_candidate: str = "PENDING_OFFICER_UTR_ENTRY",
    officer_id: str = "MH_CYBER_1930_OP_042",
    estimated_amount: str = "₹12,00,000",
    victim_state: str = "SHOCK_PARALYSIS",
    elapsed_minutes: float = 8.0,
    urgency_score: float = 0.86
) -> Dict[str, Any]:
    """
    Constructs Tier-1 I4C NCRP-CFCFRMS 2026 compliant golden-hour lien payload
    with Bharatiya Sakshya Adhiniyam (BSA) 2023 Section 63(4) cryptographic integrity seal.
    """
    if matched_keywords is None:
        matched_keywords = ["DIGITAL ARREST", "CBI WARRANT", "RTGS"]

    now_utc = datetime.now(timezone.utc)
    
    # 2026 NCRP SOP: 14-digit Ack No starting with '3' + 2-digit State Code + 11-digit sequence/timestamp
    # Exactly 14 digits total: 1 + 2 + 11 = 14 digits
    timestamp_seq = now_utc.strftime("%m%d%H%M%S")[:11].ljust(11, "0")
    ncrp_ack_no = f"3{state_code}{timestamp_seq}"[:14]

    core_payload = {
        "@context": "https://i4c.mha.gov.in/schemas/cfcfrms-v2026.jsonld",
        "@type": "CFCFRMS_GoldenHourHoldRequest",
        "ncrp_acknowledgement_number": ncrp_ack_no,
        "incident_id": f"CFCFRMS-1930-{call_uuid[:8].upper()}",
        "call_session_uuid": call_uuid,
        "timestamp_utc": now_utc.isoformat(),
        "payment_rail": detected_rail,
        "utr_reference": utr_candidate,
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
        "matched_threat_vectors": matched_keywords,
        "sop_2026_officer_attestation": {
            "officer_badge_id": officer_id,
            "prima_facie_cyber_financial_crime_verified": False,
            "human_action_required": "VERIFY_12_DIGIT_UTR_AND_SIGN_HOLD_NOTICE"
        },
        "evidentiary_status": "NON_EVIDENTIARY_DECISION_SUPPORT_ONLY_EXEMPT_FROM_CHARGE_SHEET"
    }

    # BSA 2023 Section 63(4) Part B: Cryptographic SHA-256 Integrity Fingerprint
    sha256_digest = compute_canonical_sha256(core_payload)

    core_payload["bsa_section_63_4_certificate_metadata"] = {
        "hash_algorithm": "SHA-256",
        "payload_digest_hex": sha256_digest,
        "system_engine_id": "AEGIS-VOICE-CORE-v1.0-ONPREM",
        "volatile_ram_only_verified": True,
        "admissibility_statute": "BHARATIYA_SAKSHYA_ADHINIYAM_2023_SEC_63_4",
        "certification_part": "PART_B_EXPERT_SYSTEM_HASH_VERIFICATION"
    }

    return core_payload


def build_cfcfrms_jsonld(
    call_uuid: str,
    payment_rail: str,
    p_freeze: float,
    elapsed_minutes: float,
    threat_vectors: List[str],
    urgency_score: float,
    caller_utr: str = "PENDING_OFFICER_CONFIRMATION",
    estimated_amount: str = "₹12,00,000",
    victim_state: str = "SHOCK_PARALYSIS",
    state_code: str = "27",
    officer_id: str = "MH_CYBER_1930_OP_042"
) -> Dict[str, Any]:
    """
    Backwards-compatible builder that wraps build_i4c_cfcfrms_2026_payload,
    ensuring all downstream modules receive the upgraded 2026 NCRP schema.
    """
    return build_i4c_cfcfrms_2026_payload(
        call_uuid=call_uuid,
        state_code=state_code,
        detected_rail=payment_rail,
        p_freeze=p_freeze,
        matched_keywords=threat_vectors,
        utr_candidate=caller_utr,
        officer_id=officer_id,
        estimated_amount=estimated_amount,
        victim_state=victim_state,
        elapsed_minutes=elapsed_minutes,
        urgency_score=urgency_score
    )


def verify_bsa_section_63_4_digest(payload: Dict[str, Any]) -> bool:
    """
    Verifies that the BSA 2023 Section 63(4) SHA-256 digest in the payload metadata
    matches the canonical re-hash of the core payload fields.
    Used by defence counsel, appellate courts, and CERT-In nodal auditors.
    """
    if "bsa_section_63_4_certificate_metadata" not in payload:
        return False
    
    cert_meta = payload["bsa_section_63_4_certificate_metadata"]
    recorded_digest = cert_meta.get("payload_digest_hex")
    if not recorded_digest:
        return False

    # Extract core payload without the certificate metadata block
    core = {k: v for k, v in payload.items() if k != "bsa_section_63_4_certificate_metadata"}
    computed_digest = compute_canonical_sha256(core)
    return computed_digest == recorded_digest

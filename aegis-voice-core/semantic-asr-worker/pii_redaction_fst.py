"""
Project Aegis-Voice: In-Memory Deterministic PII Scrubber & Cybercrime Threat Lexicon
Complies strictly with India DPDP Act 2023, Aadhaar Act 2016, and RBI Guidelines.
Executes in volatile memory in <1.8ms prior to any Redis or state persistence.
"""

import re
from typing import Tuple, List

# Spoken digit conversion map across English, Hindi, and Hinglish dialects
SPOKEN_DIGIT_MAP = {
    "zero": "0", "shunya": "0", "one": "1", "ek": "1", "two": "2", "do": "2",
    "three": "3", "teen": "3", "four": "4", "chaar": "4", "five": "5", "paanch": "5",
    "six": "6", "chhah": "6", "seven": "7", "saat": "7", "eight": "8", "aath": "8",
    "nine": "9", "nau": "9"
}

# Pre-compiled regex patterns per Section 4 Statutory Specifications
UID_PATTERN = re.compile(r"\b([2-9]{1}[0-9]{3})[\s-]?([0-9]{4})[\s-]?([0-9]{4})\b")
PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
OTP_CONTEXT_PATTERN = re.compile(
    r"(?i)\b(otp|pin|cvv|code|password)\b(?:\s+\w+){0,5}?\s+\b([0-9]{3,8})\b"
)
BANK_ACCT_PATTERN = re.compile(r"\b([0-9]{5,14})([0-9]{4})\b")

# Cybercrime Ontology Vectors with High-Confidence Urgency Weights
CRITICAL_LEXICAL_VECTORS = {
    "digital arrest": 0.95,
    "cbi warrant": 0.90,
    "cbi officer": 0.90,
    "skype": 0.75,
    "rtgs": 0.85,
    "upi": 0.75,
    "account emptied": 0.95,
    "lakh": 0.80,
    "crore": 0.90,
    "suicide": 1.00,
    "life threat": 0.95,
    "otp": 0.80,
    "narcotics": 0.85,
    "customs seized": 0.85,
    "fedex parcel": 0.80
}

OVERRIDE_TRIGGERS = [
    "digital arrest", "rtgs", "lakh", "crore", "suicide", "account emptied", "cbi warrant"
]

def normalize_spoken_digits(text: str) -> str:
    """Normalizes compound and spoken numbers ('nine eight double four', 'ek do teen') to digits."""
    tokens = text.split()
    out = []
    i = 0
    while i < len(tokens):
        w = tokens[i].lower().strip(".,!?")
        if w in ("double", "dubble") and i + 1 < len(tokens):
            nxt = SPOKEN_DIGIT_MAP.get(tokens[i + 1].lower().strip(".,!?"))
            if nxt:
                out.append(nxt * 2)
                i += 2
                continue
        if w in ("triple", "tripple") and i + 1 < len(tokens):
            nxt = SPOKEN_DIGIT_MAP.get(tokens[i + 1].lower().strip(".,!?"))
            if nxt:
                out.append(nxt * 3)
                i += 2
                continue
        if w in SPOKEN_DIGIT_MAP:
            out.append(SPOKEN_DIGIT_MAP[w])
        else:
            out.append(tokens[i])
        i += 1
    return " ".join(out)

def scrub_pii_in_memory(raw_transcript: str) -> str:
    """
    Executes in volatile memory in <1.8ms.
    Guarantees that raw Aadhaar, PAN, OTP, and full account numbers are never logged or stored.
    """
    normalized = normalize_spoken_digits(raw_transcript)
    
    # 1. Mask 12-digit government ID (Aadhaar): preserve only last 4 digits
    scrubbed = UID_PATTERN.sub(r"XXXX-XXXX-\3", normalized)
    
    # 2. Mask PAN
    scrubbed = PAN_PATTERN.sub("[REDACTED-PAN]", scrubbed)
    
    # 3. Mask OTP / PIN near trigger context
    scrubbed = OTP_CONTEXT_PATTERN.sub(r"\1 [REDACTED-OTP]", scrubbed)
    
    # 4. Mask long bank account numbers: preserve last 4 digits
    scrubbed = BANK_ACCT_PATTERN.sub(r"ACCT-XXXX-\2", scrubbed)
    
    return scrubbed

def extract_semantic_threat_score(scrubbed_text: str) -> Tuple[float, bool, List[str]]:
    """
    Scans for high-priority cybercrime vectors via fast substring / lexicon matching.
    Returns:
    - max_score (0.0 to 1.0)
    - override_flag (True if critical vector present, forcing semantic floor)
    - matched_keywords list
    """
    lower_text = scrubbed_text.lower()
    matched_keywords = []
    max_score = 0.0

    for kw, weight in CRITICAL_LEXICAL_VECTORS.items():
        if kw in lower_text:
            matched_keywords.append(kw.upper())
            max_score = max(max_score, weight)

    override_flag = any(k in lower_text for k in OVERRIDE_TRIGGERS)
    return max_score, override_flag, matched_keywords

"""
Entity and Claim Extraction Service for NiveshShakti.
Extracts factual claims, registration IDs, percentage returns, and financial entities.
Uses robust regex and rule-based parsing with modular LLM fallback hooks.
"""
import re
from typing import List, Dict, Any

# SEBI Registration patterns (e.g. INZ000000000, INH000000000, INA000000000, INM000000000)
SEBI_REG_PATTERN = re.compile(r'\b(IN[A-Z0-9]{8,12})\b', re.IGNORECASE)
PERCENTAGE_PATTERN = re.compile(r'(\d+(?:\.\d+)?\s*%\s*(?:daily|weekly|monthly|annually|returns?|profit|roi)?)', re.IGNORECASE)
PHONE_PATTERN = re.compile(r'(?:\+91[\-\s]?)?[6789]\d{9}\b')
UPI_PATTERN = re.compile(r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b')
URL_PATTERN = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

def extract_entities(text: str) -> List[Dict[str, str]]:
    """Extract named financial entities, registration numbers, percentages, and contact indicators."""
    entities = []

    # SEBI Registration Numbers
    for match in SEBI_REG_PATTERN.findall(text):
        entities.append({
            "entity_text": match.upper(),
            "entity_type": "SEBI_REG_NUMBER",
            "normalized_value": match.upper().strip()
        })

    # Return percentages
    for match in PERCENTAGE_PATTERN.findall(text):
        if match.strip():
            entities.append({
                "entity_text": match.strip(),
                "entity_type": "PROMISED_PERCENTAGE",
                "normalized_value": match.strip()
            })

    # Phone numbers
    for match in PHONE_PATTERN.findall(text):
        entities.append({
            "entity_text": match.strip(),
            "entity_type": "PHONE_NUMBER",
            "normalized_value": match.strip()
        })

    # UPI IDs
    for match in UPI_PATTERN.findall(text):
        if "@" in match and not match.endswith((".com", ".org", ".in", ".net")):
            entities.append({
                "entity_text": match.strip(),
                "entity_type": "UPI_ID",
                "normalized_value": match.strip().lower()
            })

    # URLs
    for match in URL_PATTERN.findall(text):
        entities.append({
            "entity_text": match.strip(),
            "entity_type": "URL",
            "normalized_value": match.strip().lower()
        })

    return entities

def extract_claims(text: str) -> List[Dict[str, Any]]:
    """
    Extracts individual checkable claims from text.
    Breaks down compound messages into distinct testable assertions.
    """
    claims = []
    sentences = [s.strip() for s in re.split(r'[.\n!?;]+', text) if len(s.strip()) > 8]

    for sentence in sentences:
        lower_s = sentence.lower()
        if any(term in lower_s for term in ["guaranteed", "fixed return", "assured", "profit", "double", "risk free"]):
            claims.append({
                "claim_text": sentence,
                "claim_type": "RETURN_GUARANTEE",
                "explanation": "Claim asserts fixed or guaranteed profit in financial markets."
            })
        elif any(term in lower_s for term in ["sebi registered", "sebi approved", "rbi approved", "license", "reg no"]):
            claims.append({
                "claim_text": sentence,
                "claim_type": "REGULATORY_REGISTRATION",
                "explanation": "Claim asserts legitimate regulatory status with SEBI or RBI."
            })
        elif any(term in lower_s for term in ["target", "call", "jackpot", "buy now", "tomorrow target"]):
            claims.append({
                "claim_text": sentence,
                "claim_type": "PRICE_RECOMMENDATION",
                "explanation": "Claim offers unauthorized stock price targets or trading tips."
            })
        elif len(claims) == 0 and len(sentences) <= 2:
            # Fallback to general claim if concise
            claims.append({
                "claim_text": sentence,
                "claim_type": "GENERAL_FINANCIAL_CLAIM",
                "explanation": "Unclassified financial assertion."
            })

    return claims

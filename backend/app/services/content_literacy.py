"""Deterministic wording cues for financial promotion versus education."""
import re


PROMOTIONAL_CUES = (
    ("RETURN_PROMISE", re.compile(r"\b(guaranteed|assured|fixed)\s+(return|profit|income)\b", re.IGNORECASE), "Return-promise wording"),
    ("PAYMENT_REQUEST", re.compile(r"\b(pay|send|transfer|deposit)\b.{0,50}\b(upi|fee|account|money|funds)\b", re.IGNORECASE), "Payment-request wording"),
    ("URGENCY_LANGUAGE", re.compile(r"\b(act now|limited slots?|only today|urgent|last chance)\b", re.IGNORECASE), "Urgency wording"),
    ("INVITATION_TO_PRIVATE_GROUP", re.compile(r"\b(join|dm|message)\b.{0,40}\b(telegram|whatsapp|vip group|private group)\b", re.IGNORECASE), "Invitation to a private messaging group"),
)
EDUCATIONAL_CUES = (
    ("EXPLANATORY_QUESTION", re.compile(r"\b(what is|how does|how to understand|learn about)\b", re.IGNORECASE), "Explanatory question or learning wording"),
    ("RISK_DISCLOSURE", re.compile(r"\b(market risks?|risk disclosure|risks? and rewards?)\b", re.IGNORECASE), "Risk-disclosure wording"),
    ("EDUCATIONAL_CONTEXT", re.compile(r"\b(educational purpose|investor education|explains?|definition of)\b", re.IGNORECASE), "Educational-context wording"),
)


def classify_content(text: str) -> dict[str, object]:
    promotional = [
        {"code": code, "description": description, "matched_text": match.group(0)}
        for code, pattern, description in PROMOTIONAL_CUES
        if (match := pattern.search(text))
    ]
    educational = [
        {"code": code, "description": description, "matched_text": match.group(0)}
        for code, pattern, description in EDUCATIONAL_CUES
        if (match := pattern.search(text))
    ]

    if promotional and educational:
        label = "MIXED_CUES"
    elif promotional:
        label = "PROMOTIONAL_CUES"
    elif educational:
        label = "EDUCATIONAL_CUES"
    else:
        label = "UNCLEAR"

    return {"label": label, "signals": promotional + educational}

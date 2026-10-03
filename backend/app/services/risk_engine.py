"""
Deterministic Risk Engine for NiveshShakti.
Evaluates input text against known Indian financial scam patterns, high-risk promises,
unregistered entity flags, urgency tactics, and regulatory violation signatures.
"""
import re
from typing import List, Dict, Any
from ..models import RiskLevel

class RiskRule:
    def __init__(self, code: str, title: str, severity: RiskLevel, pattern: str, description: str, weight: float):
        self.code = code
        self.title = title
        self.severity = severity
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.description = description
        self.weight = weight

# Pre-defined verifiable risk patterns based on SEBI & RBI fraud alerts
RISK_RULES = [
    RiskRule(
        code="GUARANTEED_RETURNS_PROMISE",
        title="Guaranteed / Fixed High Return Promise",
        severity=RiskLevel.CRITICAL,
        pattern=r"(guaranteed\s+return|fixed\s+return|assured\s+return|100%\s+profit|pakka\s+profit|guarantee|risk\s*free\s+return|double\s+your\s+money\s+in\s+\d+|paisa\s+double)",
        description="A guaranteed or fixed-return phrase is a claim to check against the exact product terms and official disclosures. The wording alone does not establish fraud or legal status.",
        weight=35.0
    ),
    RiskRule(
        code="UNREALISTIC_PERIODIC_YIELD",
        title="Abnormally High Daily/Monthly Yield",
        severity=RiskLevel.HIGH,
        pattern=r"(\d+%\s*(daily|per\s*day|rozana|weekly|per\s*week|monthly|per\s*month)|roi\s*\d+%)",
        description="A frequent high-return claim deserves careful comparison with the exact product terms and official disclosures; wording alone cannot identify a scheme.",
        weight=25.0
    ),
    RiskRule(
        code="UNOFFICIAL_COMMUNICATION_CHANNEL",
        title="WhatsApp / Telegram Channel Tipping",
        severity=RiskLevel.HIGH,
        pattern=r"(telegram|whatsapp|dm\s+for\s+calls|free\s+jackpot\s+tips|insider\s+tips)",
        description="Private messaging can make the sender's identity and claims harder to check. Verify the person, entity, and activity independently through official routes.",
        weight=20.0
    ),
    RiskRule(
        code="PRESSURE_URGENCY_TACTIC",
        title="Artificial Urgency & Scarcity Tactic",
        severity=RiskLevel.MEDIUM,
        pattern=r"(limited\s+slots?\s+left|act\s+fast|urgent|only\s+today|offer\s+closes\s+in\s+\d+|don't\s+miss|jaldi\s+karein)",
        description="Urgency language can discourage careful review. Pause and independently check the claim before sharing information or making a payment.",
        weight=15.0
    ),
    RiskRule(
        code="UNVERIFIED_REGISTRATION_CLAIM",
        title="Unverified Regulatory Affiliation Claim",
        severity=RiskLevel.HIGH,
        pattern=r"(sebi\s+approved|govt\s+approved|certified\s+by\s+rbi|100%\s+legal\s+govt)",
        description="An approval or registration statement should be checked against the relevant official source; an official-sounding claim is not verification.",
        weight=20.0
    ),
    RiskRule(
        code="UNREGULATED_PAYMENT_CHANNEL",
        title="Personal UPI / Crypto Transfer Request",
        severity=RiskLevel.HIGH,
        pattern=r"(send\s+money\s+to\s+upi|usdt|crypto|transfer\s+to\s+personal\s+account|gpay\s+screenshot|pay\s+to\s+[a-zA-Z0-9.\-_]+@\w+)",
        description="A payment request should be checked using the institution's official instructions. A UPI handle or account name alone does not verify who controls it.",
        weight=25.0
    ),
    RiskRule(
        code="OTP_CREDENTIAL_REQUEST",
        title="OTP / Credential Solicitation",
        severity=RiskLevel.CRITICAL,
        pattern=r"(share\s+your\s+otp|enter\s+otp|send\s+otp|otp\s+dena|bank\s+password|net\s+banking\s+password|share\s+screen|screen\s+share|anydesk|teamviewer|remote\s+access)",
        description="Keep OTPs, passwords, and recovery codes private. A request to disclose them or grant device access should be treated as a serious account-security warning.",
        weight=40.0
    ),
    RiskRule(
        code="IMPERSONATION_CLAIM",
        title="Regulatory Authority Impersonation",
        severity=RiskLevel.CRITICAL,
        pattern=r"(i\s+am\s+from\s+sebi|calling\s+from\s+rbi|nse\s+authority|bse\s+compliance\s+officer|income\s+tax\s+department|enforcement\s+directorate|police\s+will|arrest\s+warrant)",
        description="A claimed official identity or threat should be checked independently using contact details published by the institution, not the sender's link or number.",
        weight=40.0
    ),
    RiskRule(
        code="RECOVERY_SCAM",
        title="Investment Recovery Scam",
        severity=RiskLevel.CRITICAL,
        pattern=r"(recover\s+your\s+lost\s+money|get\s+back\s+your\s+investment|refund\s+your\s+loss|compensation\s+for\s+fraud|we\s+will\s+recover|loss\s+recovery\s+agent)",
        description="A promise to recover funds, especially in return for advance payment or account access, needs independent checking. Do not assume the recovery claim is genuine.",
        weight=35.0
    ),
    RiskRule(
        code="SOCIAL_MEDIA_SOLICITATION",
        title="Social Media / Influencer Investment Solicitation",
        severity=RiskLevel.HIGH,
        pattern=r"(instagram\s+trader|youtube\s+channel\s+tips|facebook\s+group\s+signals|twitter\s+calls|social\s+media\s+trading|influencer\s+tips|tiktok\s+trading)",
        description="A social-media post does not establish the author's identity, credentials, or whether a particular activity is covered by registration requirements.",
        weight=20.0
    ),
    RiskRule(
        code="MISLEADING_FINANCIAL_CLAIM",
        title="Misleading Historical Performance Claim",
        severity=RiskLevel.MEDIUM,
        pattern=r"(past\s+performance\s+guarantee|100%\s+accuracy|never\s+a\s+loss|zero\s+loss|track\s+record\s+of\s+100|all\s+calls\s+profit)",
        description="Accuracy or zero-loss statements need verifiable context, methodology, and source records; a message alone cannot substantiate them.",
        weight=20.0
    )
]

def evaluate_risk(text: str) -> Dict[str, Any]:
    """
    Evaluates input text and returns detected risk indicators, weighted risk score, and overall risk tier.
    """
    detected_indicators = []
    total_score = 0.0

    for rule in RISK_RULES:
        matches = rule.pattern.findall(text)
        if matches:
            # Extract snippet of evidence
            search_match = rule.pattern.search(text)
            start = max(0, search_match.start() - 20)
            end = min(len(text), search_match.end() + 20)
            snippet = text[start:end].strip()

            detected_indicators.append({
                "indicator_code": rule.code,
                "title": rule.title,
                "severity": rule.severity,
                "evidence_snippet": snippet,
                "description": rule.description
            })
            total_score += rule.weight

    # Normalize score to 0 - 100 range
    final_score = min(100.0, total_score)

    if final_score >= 60.0:
        risk_level = RiskLevel.CRITICAL
        pause_recommendation = (
            "CRITICAL RISK DETECTED: Do NOT transfer funds, share OTPs, or click investment links. "
            "This communication contains severe red flags characteristic of unapproved financial schemes."
        )
    elif final_score >= 35.0:
        risk_level = RiskLevel.HIGH
        pause_recommendation = (
            "HIGH RISK: Pause before taking any action. Verify the entity's SEBI registration number "
            "directly on the official SEBI portal before proceeding."
        )
    elif final_score >= 15.0:
        risk_level = RiskLevel.MEDIUM
        pause_recommendation = (
            "CAUTION ADVISED: Exercise due diligence and review official disclosure documents. "
            "Check that communication came from verified official domains."
        )
    else:
        risk_level = RiskLevel.LOW
        pause_recommendation = "No listed warning phrases were detected. This is not evidence that the content or entity is safe; verify important claims through official sources."

    return {
        "score": final_score,
        "level": risk_level,
        "indicators": detected_indicators,
        "pause_recommendation": pause_recommendation
    }

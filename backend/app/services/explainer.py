"""
Explanation and Education generator for NiveshShakti.
Produces tailored, jargon-free explanations across Beginner, Intermediate, Advanced levels,
as well as Hindi language support.
"""
from typing import Dict, Any, List

def generate_multi_tier_explanations(
    text: str,
    risk_data: Dict[str, Any],
    claims: List[Dict[str, Any]],
    entities: List[Dict[str, Any]]
) -> Dict[str, str]:
    """Generates educational explanations tailored to the investor's knowledge level and Hindi."""
    risk_level = risk_data.get("level", "LOW")
    risk_level = getattr(risk_level, "value", risk_level)
    score = risk_data.get("score", 0.0)
    indicators = risk_data.get("indicators", [])

    indicator_titles = [ind["title"] for ind in indicators]
    titles_summary = ", ".join(indicator_titles) if indicator_titles else "No immediate high-risk phrases"

    # Beginner explanation: Simple analogies, focus on safety and clear action
    beginner = (
        f"This text was checked for wording patterns. The rules matched {len(indicators)} cue(s): {titles_summary}. "
        "These cues do not prove fraud or safety. Check important claims through an official source such as SEBI, "
        "and do not share OTPs, passwords, or remote access."
    )

    # Intermediate explanation: Regulatory context (SEBI Act, PFUTP Regulations)
    intermediate = (
        f"Rule-based indicator score: {score}/100 ({risk_level}); this is not a probability or a legal finding. "
        f"Matched wording cues: {titles_summary}. Automated source checks may be unavailable, so verify the relevant "
        "entity directly through SEBI's official intermediary route before relying on registration claims."
    )

    # Advanced explanation: Due diligence, forensic indicators, and compliance structure
    advanced = (
        f"The deterministic rules matched these text patterns: {titles_summary}. "
        f"Indicator score: {score:.1f}/100; it is not a scam probability, verification result, or determination of legal compliance. "
        "Review the original context and seek current information from the relevant official source."
    )

    # Hindi explanation: Native phrasing for Bharat retail investors
    hindi = (
        f"इस पाठ में नियमों ने {len(indicators)} शब्द-संकेत पहचाने: {titles_summary}। "
        "ये संकेत धोखाधड़ी या सुरक्षा का प्रमाण नहीं हैं। सेबी (SEBI) जैसे आधिकारिक स्रोत पर दावे की जाँच करें और OTP या पासवर्ड साझा न करें।"
    )
    hindi_intermediate = (
        f"नियम-आधारित जाँच में {len(indicators)} संकेत मिले: {titles_summary}। "
        f"सूचकांक {score}/100 ({risk_level}) है; यह धोखाधड़ी की संभावना या कानूनी निष्कर्ष नहीं है। "
        "दावे और संस्था को संबंधित आधिकारिक स्रोत पर अलग से जाँचें।"
    )
    hindi_advanced = (
        f"पद्धति: निर्धारित नियमों ने {len(indicators)} शब्द-संकेत मिलाए ({titles_summary}); "
        f"सूचकांक {score:.1f}/100 है। यह संभावना, नियामकीय पुष्टि या कानूनी स्थिति नहीं बताता। "
        "मूल संदेश का संदर्भ और आधिकारिक दस्तावेज़ स्वयं जाँचें।"
    )
    hinglish = (
        f"Is text mein rules ne {len(indicators)} wording cue(s) match kiye: {titles_summary}. "
        "Yeh cues fraud ya safety ka proof nahi hain. SEBI ke official route par relevant claim verify karein; "
        "OTP, password ya remote access share na karein."
    )
    hinglish_intermediate = (
        f"Rules ne {len(indicators)} wording cues match kiye: {titles_summary}. "
        f"Indicator score {score}/100 ({risk_level}) hai; yeh fraud probability ya legal finding nahi hai. "
        "Relevant claim ko official source par alag se verify karein."
    )
    hinglish_advanced = (
        f"Method: deterministic rules ne {len(indicators)} text cues match kiye ({titles_summary}); "
        f"indicator score {score:.1f}/100 hai. Yeh probability, regulatory confirmation, ya legal conclusion nahi hai. "
        "Original context aur official documents independently check karein."
    )

    return {
        "beginner": beginner,
        "intermediate": intermediate,
        "advanced": advanced,
        "hindi": hindi,
        "hindi_intermediate": hindi_intermediate,
        "hindi_advanced": hindi_advanced,
        "hinglish": hinglish,
        "hinglish_intermediate": hinglish_intermediate,
        "hinglish_advanced": hinglish_advanced,
    }

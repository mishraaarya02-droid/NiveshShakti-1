"""
Analysis pipeline orchestrator for NiveshShakti.
Coordinates Extraction, Risk Engine, Source Verification, and Multi-Tier Explanation.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import (
    Analysis,
    Claim,
    RiskIndicator,
    ExtractedEntity,
    VerificationResult,
    EvidenceItem,
    Source,
    AnalysisStatus,
    VerificationStatus,
)
from .extraction import extract_entities, extract_claims
from .risk_engine import evaluate_risk
from .sources import ADAPTER_REGISTRY
from .explainer import generate_multi_tier_explanations
from .normalization import normalize_extracted_text
from .content_literacy import classify_content

async def run_analysis_pipeline(analysis_id: int, text: str, db: Session) -> Analysis:
    """
    Executes the full verification pipeline on extracted/submitted text:
    1. Extract financial entities (SEBI reg numbers, percentages, phones, UPIs)
    2. Extract checkable claims
    3. Run deterministic risk scoring engine
    4. Verify claims against authoritative source adapters
    5. Generate multi-tier beginner/intermediate/advanced and Hindi explanations
    6. Persist results in DB transaction
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise ValueError(f"Analysis {analysis_id} not found")

    analysis.status = AnalysisStatus.PROCESSING
    text, detected_language = normalize_extracted_text(text)
    analysis.extracted_text = text
    analysis.detected_language = detected_language
    content_literacy = classify_content(text)
    analysis.content_classification = content_literacy["label"]
    analysis.content_signals = content_literacy["signals"]
    db.commit()

    # Step 1: Extract entities
    raw_entities = extract_entities(text)
    for ent in raw_entities:
        db_ent = ExtractedEntity(
            analysis_id=analysis.id,
            entity_text=ent["entity_text"],
            entity_type=ent["entity_type"],
            normalized_value=ent["normalized_value"]
        )
        db.add(db_ent)

    # Step 2: Extract claims
    raw_claims = extract_claims(text)
    db_claims = []
    for cl in raw_claims:
        db_cl = Claim(
            analysis_id=analysis.id,
            claim_text=cl["claim_text"],
            claim_type=cl.get("claim_type"),
            verification_status=VerificationStatus.UNVERIFIED,
            explanation=cl.get("explanation")
        )
        db.add(db_cl)
        db_claims.append(db_cl)
    db.flush()

    # Step 3: Run deterministic risk scoring engine
    risk_data = evaluate_risk(text)
    analysis.overall_risk_score = risk_data["score"]
    analysis.overall_risk_level = risk_data["level"]
    analysis.pause_recommendation = risk_data["pause_recommendation"]

    for ind in risk_data["indicators"]:
        db_ind = RiskIndicator(
            analysis_id=analysis.id,
            indicator_code=ind["indicator_code"],
            title=ind["title"],
            severity=ind["severity"],
            evidence_snippet=ind["evidence_snippet"],
            description=ind["description"]
        )
        db.add(db_ind)

    # Step 4: Verify claims against authoritative source adapters
    # Ensure source records exist in DB
    for adapter_code, adapter in ADAPTER_REGISTRY.items():
        db_source = db.query(Source).filter(Source.code == adapter_code).first()
        if not db_source:
            db_source = Source(
                code=adapter_code,
                name=adapter.name,
                url=adapter.manual_url,
                source_type=adapter.source_type,
                health_status="UNKNOWN",
                last_retrieval_status="NOT_CHECKED",
            )
            db.add(db_source)
            db.flush()

        # Check each claim against adapter
        for db_cl in db_claims:
            verification_outcome = await adapter.verify(query=db_cl.claim_text)
            ver_res = VerificationResult(
                claim_id=db_cl.id,
                source_id=db_source.id,
                source_name=db_source.name,
                source_code=db_source.code,
                status=verification_outcome["status"],
                source_type=db_source.source_type,
                retrieval_status=verification_outcome.get("retrieval_status"),
                evidence_text=verification_outcome["evidence_text"],
                source_published_at=verification_outcome.get("source_published_at"),
                source_version=verification_outcome.get("source_version"),
                query_used=verification_outcome.get("query_used"),
                source_url=verification_outcome.get("source_url")
            )
            db.add(ver_res)
            db.add(EvidenceItem(
                analysis_id=analysis.id,
                verification_result=ver_res,
                source_name=db_source.name,
                source_code=db_source.code,
                source_type=db_source.source_type,
                status=verification_outcome["status"],
                retrieval_status=verification_outcome.get("retrieval_status"),
                evidence_text=verification_outcome["evidence_text"],
                source_url=verification_outcome.get("source_url"),
                source_published_at=verification_outcome.get("source_published_at"),
                source_version=verification_outcome.get("source_version"),
            ))
            # Default claim to SOURCE_UNAVAILABLE when verified with live adapter returning SOURCE_UNAVAILABLE
            db_cl.verification_status = verification_outcome["status"]

    # Step 5: Multi-tier educational explanations
    explanations = generate_multi_tier_explanations(text, risk_data, raw_claims, raw_entities)
    analysis.explanation_beginner = explanations["beginner"]
    analysis.explanation_intermediate = explanations["intermediate"]
    analysis.explanation_advanced = explanations["advanced"]
    analysis.explanation_hindi = explanations["hindi"]
    analysis.explanation_hindi_intermediate = explanations["hindi_intermediate"]
    analysis.explanation_hindi_advanced = explanations["hindi_advanced"]
    analysis.explanation_hinglish = explanations["hinglish"]
    analysis.explanation_hinglish_intermediate = explanations["hinglish_intermediate"]
    analysis.explanation_hinglish_advanced = explanations["hinglish_advanced"]

    # Finalize analysis
    analysis.status = AnalysisStatus.COMPLETED
    db.commit()
    db.refresh(analysis)
    return analysis

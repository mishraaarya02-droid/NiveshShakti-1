"""
Test suite for NiveshShakti backend:
- Password hashing & JWT authentication
- Risk Engine scoring & rule evaluation
- Claim & Entity extraction
- Authoritative Source adapters (contract validation: SOURCE_UNAVAILABLE)
- Analysis pipeline end-to-end integration
- SSRF URL validation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User, Language, KnowledgeLevel, VerificationStatus, RiskLevel
from app.core.security import get_password_hash, verify_password, create_access_token
from app.services.risk_engine import evaluate_risk
from app.services.extraction import extract_entities, extract_claims
from app.services.sources import SEBIIntermediaryAdapter, RBISachetAdapter
from app.services.pipeline import run_analysis_pipeline
from app.services.explainer import generate_multi_tier_explanations
from app.api.analysis import validate_url_safety
from fastapi import HTTPException

# In-memory test SQLite DB
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_password_hashing():
    pw = "SuperSecurePassword123"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_long_password_suffix_is_not_discarded():
    first_password = "a" * 72 + "first"
    second_password = "a" * 72 + "second"
    hashed = get_password_hash(first_password)

    assert verify_password(first_password, hashed) is True
    assert verify_password(second_password, hashed) is False

def test_jwt_token_generation():
    token = create_access_token({"sub": "investor@arthsutra.in", "user_id": 1})
    assert isinstance(token, str)
    assert len(token) > 20

def test_risk_engine_guaranteed_return_detection():
    scam_msg = (
        "Join our Telegram channel now! 100% guaranteed return with 10% daily profit. "
        "Limited slots left, act fast. Paisa double in 15 days."
    )
    result = evaluate_risk(scam_msg)
    assert result["score"] >= 60.0
    assert result["level"] == RiskLevel.CRITICAL
    assert len(result["indicators"]) >= 2
    codes = [ind["indicator_code"] for ind in result["indicators"]]
    assert "GUARANTEED_RETURNS_PROMISE" in codes
    assert "UNOFFICIAL_COMMUNICATION_CHANNEL" in codes
    assert "PRESSURE_URGENCY_TACTIC" in codes

def test_risk_engine_safe_message():
    safe_msg = "Please find the monthly statement for your index mutual fund SIP attached."
    result = evaluate_risk(safe_msg)
    assert result["score"] < 15.0
    assert result["level"] == RiskLevel.LOW
    assert len(result["indicators"]) == 0

def test_entity_and_claim_extraction():
    text = (
        "Our SEBI registration number is INH000001234. "
        "We offer guaranteed 25% profit monthly. Call +919876543210 or UPI to payment@ybl"
    )
    entities = extract_entities(text)
    types = [e["entity_type"] for e in entities]
    assert "SEBI_REG_NUMBER" in types
    assert "PROMISED_PERCENTAGE" in types
    assert "PHONE_NUMBER" in types
    assert "UPI_ID" in types

    claims = extract_claims(text)
    claim_types = [c["claim_type"] for c in claims]
    assert "RETURN_GUARANTEE" in claim_types or "REGULATORY_REGISTRATION" in claim_types


def test_explanations_have_language_and_knowledge_level_variants():
    explanations = generate_multi_tier_explanations(
        "A financial claim",
        {"level": "LOW", "score": 0.0, "indicators": []},
        [],
        [],
    )
    keys = (
        "beginner",
        "intermediate",
        "advanced",
        "hindi",
        "hindi_intermediate",
        "hindi_advanced",
        "hinglish",
        "hinglish_intermediate",
        "hinglish_advanced",
    )

    assert all(explanations[key] for key in keys)
    assert all("RiskLevel." not in explanations[key] for key in keys)
    assert len({explanations[key] for key in keys[:3]}) == 3
    assert len({explanations[key] for key in keys[3:6]}) == 3
    assert len({explanations[key] for key in keys[6:]}) == 3

@pytest.mark.asyncio
async def test_sebi_source_adapter_contract():
    adapter = SEBIIntermediaryAdapter()
    res = await adapter.verify("INH000001234")
    # Must never fabricate data; returns SOURCE_UNAVAILABLE when not integrated with private token
    assert res["status"] == VerificationStatus.SOURCE_UNAVAILABLE
    assert "sebi" in res["evidence_text"].lower()

@pytest.mark.asyncio
async def test_analysis_pipeline_e2e(db_session):
    # Create user
    user = User(
        email="test_investor@example.com",
        hashed_password="hashed_placeholder",
        language=Language.EN,
        knowledge_level=KnowledgeLevel.BEGINNER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create Analysis
    from app.models import Analysis, AnalysisStatus
    analysis = Analysis(
        user_id=user.id,
        input_type="text",
        raw_input="Join VIP Telegram! 100% guaranteed return pakka profit. Pay to vip@upi",
        status=AnalysisStatus.PENDING
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    # Run pipeline
    completed = await run_analysis_pipeline(analysis_id=analysis.id, text=analysis.raw_input, db=db_session)
    assert completed.status == AnalysisStatus.COMPLETED
    assert completed.overall_risk_score > 35.0
    assert len(completed.risk_indicators) >= 2
    assert completed.explanation_beginner is not None
    assert completed.explanation_hindi is not None
    assert "गारंटीड" in completed.explanation_hindi or "सेबी" in completed.explanation_hindi

def test_ssrf_protection():
    with pytest.raises(HTTPException):
        validate_url_safety("http://localhost:8000/admin")
    with pytest.raises(HTTPException):
        validate_url_safety("http://127.0.0.1:5432")
    with pytest.raises(HTTPException):
        validate_url_safety("http://127.1:5432")
    with pytest.raises(HTTPException):
        validate_url_safety("http://0x7f000001:5432")
    with pytest.raises(HTTPException):
        validate_url_safety("http://[::1]:8000")
    with pytest.raises(HTTPException):
        validate_url_safety("http://user:pass@investor.sebi.gov.in/")
    with pytest.raises(HTTPException):
        validate_url_safety("http://investor.localhost/")
    with pytest.raises(HTTPException):
        validate_url_safety("ftp://malicious.com")
    # Valid external URL should not raise
    validate_url_safety("https://investor.sebi.gov.in")

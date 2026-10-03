"""
End-to-end API and Integration verification script for NiveshShakti.
Directly tests:
1. User registration & duplicate registration validation
2. User authentication (JWT issuance & invalid credential rejection)
3. Authenticated profile endpoint (/auth/me)
4. Unauthenticated access protection (401 response on protected routes)
5. Text analysis with scam signals (guaranteed returns, Telegram tipping, UPI handle)
6. URL analysis with SSRF safety checks (rejection of localhost/127.0.0.1)
7. Analysis history retrieval
8. Analysis detail retrieval by ID
9. Source registry health checks
10. Honest SOURCE_UNAVAILABLE evidence status handling without mock/fabrication
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import AnalysisStatus, RiskLevel, VerificationStatus

# Isolated test database
TEST_DB_URL = "sqlite:///./test_verification_run.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("./test_verification_run.db"):
        try:
            os.remove("./test_verification_run.db")
        except Exception:
            pass

client = TestClient(app)

def test_full_auth_lifecycle():
    # 1. Register new user
    reg_payload = {
        "email": "investor_check@niveshshakti.org",
        "password": "StrongPassword!2026",
        "language": "HI",
        "knowledge_level": "BEGINNER"
    }
    res = client.post("/auth/register", json=reg_payload)
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["email"] == "investor_check@niveshshakti.org"
    assert user_data["language"] == "HI"
    assert user_data["knowledge_level"] == "BEGINNER"

    # 2. Duplicate registration rejected
    res_dup = client.post("/auth/register", json=reg_payload)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"]

    # 3. Wrong password rejected
    res_wrong = client.post("/auth/login", json={"email": reg_payload["email"], "password": "WrongPassword"})
    assert res_wrong.status_code == 401

    # 4. Successful login returns JWT
    res_login = client.post("/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]})
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 5. Access /auth/me with Bearer token
    res_me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "investor_check@niveshshakti.org"

    # 6. Access without token rejected
    res_unauth = client.get("/auth/me")
    assert res_unauth.status_code == 401

def test_text_analysis_and_evidence_handling():
    # Login to get token
    login_res = client.post("/auth/login", json={
        "email": "investor_check@niveshshakti.org",
        "password": "StrongPassword!2026"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit suspicious message
    scam_text = (
        "EXCLUSIVE: Join our VIP Telegram group for 100% guaranteed return with pakka profit! "
        "Pay registration fee to admin@ybl immediately. Limited slots left, act fast!"
    )
    res = client.post("/analysis/text", json={"text": scam_text}, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["status"] == "COMPLETED"
    assert data["overall_risk_score"] >= 60.0
    assert data["overall_risk_level"] in ["CRITICAL", "HIGH"]
    assert data["pause_recommendation"] is not None
    assert "CRITICAL RISK" in data["pause_recommendation"] or "HIGH RISK" in data["pause_recommendation"]

    # Verify risk indicators
    ind_codes = [ind["indicator_code"] for ind in data["risk_indicators"]]
    assert "GUARANTEED_RETURNS_PROMISE" in ind_codes
    assert "UNOFFICIAL_COMMUNICATION_CHANNEL" in ind_codes
    assert "PRESSURE_URGENCY_TACTIC" in ind_codes

    # Verify entities extracted
    ent_types = [ent["entity_type"] for ent in data["entities"]]
    assert "UPI_ID" in ent_types

    # Verify claims and authoritative source results (honest SOURCE_UNAVAILABLE)
    assert len(data["claims"]) >= 1
    for claim in data["claims"]:
        assert claim["verification_status"] == VerificationStatus.SOURCE_UNAVAILABLE
        for vr in claim["verification_results"]:
            assert vr["status"] == VerificationStatus.SOURCE_UNAVAILABLE
            assert vr["evidence_text"] is not None
            assert vr["source_code"] in ["SEBI_INTERMEDIARIES", "SEBI_INVESTOR", "NSDL", "RBI_SACHET"]

    # Verify multi-tier explanations
    assert "SEBI" in data["explanation_beginner"] or "guaranteed" in data["explanation_beginner"]
    assert "सेबी" in data["explanation_hindi"] or "गारंटीड" in data["explanation_hindi"]

    analysis_id = data["id"]

    # Test retrieval by ID
    res_get = client.get(f"/analysis/{analysis_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == analysis_id

    # Test user history
    res_hist = client.get("/analysis/user/history", headers=headers)
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) >= 1
    assert history[0]["id"] == analysis_id

def test_url_analysis_and_ssrf_rejection():
    login_res = client.post("/auth/login", json={
        "email": "investor_check@niveshshakti.org",
        "password": "StrongPassword!2026"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # SSRF Attack attempts rejected
    res_local = client.post("/analysis/url", json={"url": "http://127.0.0.1:8000/api"}, headers=headers)
    assert res_local.status_code == 400
    assert "Forbidden target host" in res_local.json()["detail"]

    res_meta = client.post("/analysis/url", json={"url": "http://169.254.169.254/latest/meta-data"}, headers=headers)
    assert res_meta.status_code == 400
    assert "Forbidden target host" in res_meta.json()["detail"]

    # Valid external URL processed
    res_valid = client.post("/analysis/url", json={"url": "https://investor.sebi.gov.in"}, headers=headers)
    assert res_valid.status_code == 201
    assert res_valid.json()["status"] == "COMPLETED"
    assert "destination page not fetched" in res_valid.json()["extracted_text"]

def test_sources_health_endpoint():
    res = client.get("/analysis/sources/health")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 2
    codes = [s["code"] for s in sources]
    assert "SEBI_INTERMEDIARIES" in codes
    assert "RBI_SACHET" in codes
    for s in sources:
        assert s["health_status"] in ["AVAILABLE", "DEGRADED", "UNAVAILABLE"]

"""Tests for official-source contracts and authenticated investor workflows."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models import Analysis, AnalysisStatus, User
from app.services.sources import ADAPTER_REGISTRY, claim_status_for_retrieval


@pytest.fixture
def workflow_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    session = session_factory()
    owner = User(email="owner@example.test", hashed_password="unused")
    other = User(email="other@example.test", hashed_password="unused")
    session.add_all([owner, other])
    session.commit()
    session.refresh(owner)
    session.refresh(other)
    own_token = create_access_token({"sub": owner.email, "user_id": owner.id})
    other_token = create_access_token({"sub": other.email, "user_id": other.id})
    analysis = Analysis(user_id=owner.id, input_type="text", raw_input="Private message", status=AnalysisStatus.COMPLETED)
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    analysis_id = analysis.id
    session.close()

    with TestClient(app) as client:
        yield client, session_factory, own_token, other_token, analysis_id

    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.mark.asyncio
async def test_source_adapters_expose_conservative_search_retrieve_and_health_contract():
    adapter = ADAPTER_REGISTRY["SEBI_INTERMEDIARIES"]

    result = await adapter.verify("INH000001234")

    assert result["status"] == "SOURCE_UNAVAILABLE"
    assert result["retrieval_status"] == "SOURCE_UNAVAILABLE"
    assert result["source_url"].startswith("https://www.sebi.gov.in/")
    assert "manual" in result["evidence_text"].lower()
    assert callable(adapter.search)
    assert callable(adapter.retrieve)
    assert callable(adapter.health_check)


def test_missing_record_is_unverified_not_fraud():
    assert claim_status_for_retrieval("NOT_FOUND") == "UNVERIFIED"
    assert claim_status_for_retrieval("AVAILABLE") == "UNVERIFIED"
    assert claim_status_for_retrieval("SOURCE_UNAVAILABLE") == "SOURCE_UNAVAILABLE"


def test_grievance_guidance_lists_manual_official_routes(workflow_client):
    client, _, _, _, _ = workflow_client

    response = client.get("/grievance/situations")

    assert response.status_code == 200
    situations = response.json()
    assert len(situations) >= 8
    assert {item["id"] for item in situations} >= {
        "suspicious_solicitation",
        "money_paid",
        "credentials_shared",
        "impersonation",
        "misleading_information",
        "intermediary_issue",
        "investor_rights",
        "suspicious_activity",
    }
    assert all(item["official_channels"] for item in situations)
    assert all(channel["url"].startswith("https://") for item in situations for channel in item["official_channels"])


def test_analysis_delete_is_authenticated_and_owner_scoped(workflow_client):
    client, session_factory, own_token, other_token, analysis_id = workflow_client

    unauthorized = client.delete(f"/analysis/{analysis_id}")
    other_detail = client.get(
        f"/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    other_history = client.get("/analysis/user/history", headers={"Authorization": f"Bearer {other_token}"})
    forbidden = client.delete(
        f"/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    deleted = client.delete(
        f"/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {own_token}"},
    )
    repeated = client.delete(
        f"/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {own_token}"},
    )

    assert unauthorized.status_code == 401
    assert other_detail.status_code == 404
    assert other_history.status_code == 200
    assert other_history.json() == []
    assert forbidden.status_code == 404
    assert deleted.status_code == 204
    assert repeated.status_code == 404
    with session_factory() as session:
        assert session.query(Analysis).filter_by(id=analysis_id).first() is None


def test_authenticated_preferences_persist(workflow_client):
    client, _, own_token, _, _ = workflow_client
    headers = {"Authorization": f"Bearer {own_token}"}

    response = client.patch(
        "/auth/me/preferences",
        headers=headers,
        json={"language": "HI", "knowledge_level": "ADVANCED"},
    )

    assert response.status_code == 200
    assert response.json()["language"] == "HI"
    assert response.json()["knowledge_level"] == "ADVANCED"
    profile = client.get("/auth/me", headers=headers)
    assert profile.json()["language"] == "HI"
    assert profile.json()["knowledge_level"] == "ADVANCED"


def test_preferences_do_not_change_analysis_evidence(workflow_client):
    client, _, own_token, _, _ = workflow_client
    headers = {"Authorization": f"Bearer {own_token}"}
    checked = client.post(
        "/analysis/text",
        headers=headers,
        json={"text": "This document describes the service fee and includes a risk section."},
    )
    assert checked.status_code == 201
    original = checked.json()

    updated = client.patch(
        "/auth/me/preferences",
        headers=headers,
        json={"language": "HINGLISH", "knowledge_level": "ADVANCED"},
    )
    assert updated.status_code == 200
    retrieved = client.get(f"/analysis/{original['id']}", headers=headers)

    assert retrieved.status_code == 200
    changed = retrieved.json()
    assert changed["claims"] == original["claims"]
    assert changed["risk_indicators"] == original["risk_indicators"]
    assert changed["entities"] == original["entities"]
    assert changed["content_signals"] == original["content_signals"]


def test_repeated_failed_logins_are_rate_limited(workflow_client):
    client, _, _, _, _ = workflow_client
    email = "rate-limit-check@example.com"

    responses = [
        client.post("/auth/login", json={"email": email, "password": "WrongPassword!"})
        for _ in range(6)
    ]

    assert [response.status_code for response in responses] == [401, 401, 401, 401, 401, 429]
    assert responses[-1].headers["retry-after"]
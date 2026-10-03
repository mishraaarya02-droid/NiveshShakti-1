"""Multimodal upload API coverage, including explicit provider integration gates."""
import io
import os
import shutil
import wave

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import analysis as analysis_api
from app.database import Base, get_db
from app.main import app
from app.models import Analysis, AnalysisInput, User
from app.core.security import create_access_token
from app.services import ocr, speech


@pytest.fixture
def multimodal_client():
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
    user = User(email="multimodal@example.test", hashed_password="unused")
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token({"sub": user.email, "user_id": user.id})
    session.close()

    with TestClient(app) as client:
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client, session_factory

    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_image_upload_rejects_extension_mismatch_without_persisting(multimodal_client):
    client, session_factory = multimodal_client

    response = client.post(
        "/analysis/image",
        files={"file": ("offer.txt", b"not an image", "image/png")},
    )

    assert response.status_code == 415
    with session_factory() as session:
        assert session.query(Analysis).count() == 0


def test_image_upload_rejects_oversized_file_without_persisting(multimodal_client):
    client, session_factory = multimodal_client
    from app.services.ocr import MAX_FILE_SIZE_BYTES

    response = client.post(
        "/analysis/image",
        files={"file": ("offer.png", b"x" * (MAX_FILE_SIZE_BYTES + 1), "image/png")},
    )

    assert response.status_code == 413
    with session_factory() as session:
        assert session.query(Analysis).count() == 0


def make_png(text="Guaranteed 25% monthly return"):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1600, 300), "white")
    ImageDraw.Draw(image).text((40, 100), text, fill="black", stroke_width=1)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def make_wav():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * 1600)
    return stream.getvalue()


class FixedOCRProvider:
    def __init__(self, text):
        self.text = text

    def extract_text(self, image):
        return self.text


class FixedSpeechProvider:
    def __init__(self, text):
        self.text = text

    def transcribe(self, audio_path):
        assert os.path.isfile(audio_path)
        assert os.path.basename(os.path.dirname(audio_path)).startswith("niveshshakti-audio-")
        return self.text


def test_image_provider_interface_extracts_from_decoded_image():
    result = ocr.extract_text_from_image(
        make_png(),
        "image/png",
        "offer.png",
        provider=FixedOCRProvider("Guaranteed 25% monthly return"),
    )

    assert result["status"] == "SUCCESS"
    assert result["text"] == "Guaranteed 25% monthly return"


def test_image_provider_failure_is_not_reported_as_empty_success():
    class FailingProvider:
        def extract_text(self, image):
            raise RuntimeError("provider failed")

    result = ocr.extract_text_from_image(make_png(), "image/png", "offer.png", provider=FailingProvider())

    assert result["status"] == "ERROR"
    assert result["text"] is None


def test_image_rejects_malformed_content_and_reports_missing_tesseract(monkeypatch):
    malformed = ocr.extract_text_from_image(b"not a png", "image/png", "offer.png")
    assert malformed["status"] == "INVALID_INPUT"

    def reject_image_bomb(*args, **kwargs):
        raise ocr.Image.DecompressionBombWarning("oversized dimensions")

    monkeypatch.setattr(ocr.Image, "open", reject_image_bomb)
    oversized_dimensions = ocr.extract_text_from_image(make_png(), "image/png", "offer.png")
    assert oversized_dimensions["status"] == "INVALID_INPUT"

    monkeypatch.undo()
    monkeypatch.setattr(ocr, "pytesseract", None)
    unavailable = ocr.extract_text_from_image(make_png(), "image/png", "offer.png")
    assert unavailable["status"] == "PROVIDER_UNAVAILABLE"
    assert unavailable["text"] is None


def test_audio_provider_interface_transcribes_in_isolated_temp_storage():
    result = speech.transcribe_audio(
        make_wav(),
        "audio/wav",
        "voice.wav",
        provider=FixedSpeechProvider("Guaranteed returns were promised"),
    )

    assert result["status"] == "SUCCESS"
    assert result["text"] == "Guaranteed returns were promised"


def test_audio_rejects_invalid_mime_extension_and_malformed_content():
    mismatch = speech.transcribe_audio(b"audio", "audio/wav", "voice.mp3")
    malformed = speech.transcribe_audio(b"not audio", "audio/wav", "voice.wav")

    assert mismatch["status"] == "INVALID_INPUT"
    assert malformed["status"] == "INVALID_INPUT"


def test_audio_provider_unavailable_and_provider_failure_are_explicit(monkeypatch):
    monkeypatch.setattr(
        speech.WhisperSpeechProvider,
        "transcribe",
        lambda self, audio_path: (_ for _ in ()).throw(RuntimeError("Whisper dependencies are not installed")),
    )
    unavailable = speech.transcribe_audio(make_wav(), "audio/wav", "voice.wav")
    assert unavailable["status"] == "PROVIDER_UNAVAILABLE"
    assert unavailable["text"] is None

    failed = speech.transcribe_audio(
        make_wav(),
        "audio/wav",
        "voice.wav",
        provider=type("FailingProvider", (), {"transcribe": lambda self, path: 1 / 0})(),
    )
    assert failed["status"] == "ERROR"
    assert failed["text"] is None


def test_audio_upload_rejects_oversized_file_without_persisting(multimodal_client):
    client, session_factory = multimodal_client
    from app.services.speech import MAX_FILE_SIZE_BYTES

    response = client.post(
        "/analysis/audio",
        files={"file": ("voice.wav", b"x" * (MAX_FILE_SIZE_BYTES + 1), "audio/wav")},
    )

    assert response.status_code == 413
    with session_factory() as session:
        assert session.query(Analysis).count() == 0


def test_audio_upload_rejects_malformed_content_without_persisting(multimodal_client):
    client, session_factory = multimodal_client

    response = client.post(
        "/analysis/audio",
        files={"file": ("voice.wav", b"not a wav file", "audio/wav")},
    )

    assert response.status_code == 400
    with session_factory() as session:
        assert session.query(Analysis).count() == 0


def test_upload_routes_require_authentication():
    with TestClient(app) as client:
        image_response = client.post(
            "/analysis/image",
            files={"file": ("offer.png", make_png(), "image/png")},
        )
        audio_response = client.post(
            "/analysis/audio",
            files={"file": ("voice.wav", make_wav(), "audio/wav")},
        )

    assert image_response.status_code == 401
    assert audio_response.status_code == 401


def test_image_analysis_persists_extracted_text_risks_and_evidence(multimodal_client, monkeypatch):
    client, session_factory = multimodal_client
    extracted_text = "Join our Telegram group for 100% guaranteed return. Send money to demo@ybl now."
    monkeypatch.setattr(
        analysis_api,
        "extract_text_from_image",
        lambda contents, mime_type, filename: {
            "status": "SUCCESS",
            "text": extracted_text,
            "message": "OCR completed successfully.",
        },
    )

    response = client.post(
        "/analysis/image",
        files={"file": ("offer.png", make_png(), "image/png")},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "COMPLETED"
    assert result["raw_input"] == "[image upload]"
    assert result["extraction_status"] == "SUCCESS"
    assert result["detected_language"] == "EN"
    assert result["extracted_text"] == extracted_text
    assert result["risk_indicators"]
    assert result["claims"]
    assert all(claim["verification_results"] for claim in result["claims"])
    assert all(
        evidence["status"] == "SOURCE_UNAVAILABLE"
        for claim in result["claims"]
        for evidence in claim["verification_results"]
    )
    with session_factory() as session:
        persisted = session.query(Analysis).filter_by(id=result["id"]).one()
        assert persisted.extracted_text == extracted_text
        assert persisted.extraction_status == "SUCCESS"
        assert persisted.detected_language == "EN"
        assert persisted.risk_indicators
        assert persisted.claims[0].verification_results
        assert persisted.inputs[0].media_type == "image/png"
        assert persisted.inputs[0].byte_length == len(make_png())
        assert persisted.evidence_items
        assert persisted.evidence_items[0].retrieval_status == "SOURCE_UNAVAILABLE"


def test_audio_analysis_persists_transcript_risks_and_evidence(multimodal_client, monkeypatch):
    client, session_factory = multimodal_client
    transcript = "Join our Telegram group for 100% guaranteed return. Send money to demo@ybl now."
    monkeypatch.setattr(
        analysis_api,
        "transcribe_audio",
        lambda contents, mime_type, filename: {
            "status": "SUCCESS",
            "text": transcript,
            "message": "Transcription completed successfully.",
        },
    )

    response = client.post(
        "/analysis/audio",
        files={"file": ("voice.wav", make_wav(), "audio/wav")},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "COMPLETED"
    assert result["extraction_status"] == "SUCCESS"
    assert result["extracted_text"] == transcript
    assert result["risk_indicators"]
    assert result["claims"]
    assert all(claim["verification_results"] for claim in result["claims"])
    with session_factory() as session:
        persisted = session.query(Analysis).filter_by(id=result["id"]).one()
        assert persisted.extracted_text == transcript
        assert persisted.extraction_status == "SUCCESS"
        assert persisted.risk_indicators
        assert persisted.claims[0].verification_results
        assert persisted.inputs[0].media_type == "audio/wav"
        assert persisted.inputs[0].byte_length == len(make_wav())
        assert persisted.evidence_items


def test_provider_unavailable_is_persisted_without_risk_results(multimodal_client, monkeypatch):
    client, session_factory = multimodal_client
    monkeypatch.setattr(
        analysis_api,
        "extract_text_from_image",
        lambda contents, mime_type, filename: {
            "status": "PROVIDER_UNAVAILABLE",
            "text": None,
            "message": "Tesseract OCR is unavailable.",
        },
    )

    response = client.post(
        "/analysis/image",
        files={"file": ("offer.png", make_png(), "image/png")},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "FAILED"
    assert result["extraction_status"] == "PROVIDER_UNAVAILABLE"
    assert result["extracted_text"] is None
    assert result["overall_risk_score"] is None
    assert result["overall_risk_level"] is None
    assert result["claims"] == []
    assert result["risk_indicators"] == []
    history = client.get("/analysis/user/history").json()
    assert history[0]["status"] == "FAILED"
    assert history[0]["overall_risk_score"] is None
    assert history[0]["overall_risk_level"] is None
    with session_factory() as session:
        persisted = session.query(Analysis).filter_by(id=result["id"]).one()
        assert persisted.extraction_status == "PROVIDER_UNAVAILABLE"
        assert persisted.risk_indicators == []


def test_audio_provider_unavailable_is_persisted_without_analysis(multimodal_client, monkeypatch):
    client, session_factory = multimodal_client
    monkeypatch.setattr(
        analysis_api,
        "transcribe_audio",
        lambda contents, mime_type, filename: {
            "status": "PROVIDER_UNAVAILABLE",
            "text": None,
            "message": "Whisper is unavailable.",
        },
    )

    response = client.post(
        "/analysis/audio",
        files={"file": ("voice.wav", make_wav(), "audio/wav")},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "FAILED"
    assert result["extraction_status"] == "PROVIDER_UNAVAILABLE"
    assert result["extracted_text"] is None
    assert result["overall_risk_score"] is None
    assert result["overall_risk_level"] is None
    assert result["claims"] == []
    assert result["risk_indicators"] == []
    with session_factory() as session:
        persisted = session.query(Analysis).filter_by(id=result["id"]).one()
        assert persisted.extraction_status == "PROVIDER_UNAVAILABLE"
        assert persisted.risk_indicators == []


def test_real_tesseract_ocr_when_installed():
    if shutil.which("tesseract") is None:
        pytest.skip("Real-provider check requires the Tesseract binary.")

    result = ocr.extract_text_from_image(make_png(), "image/png", "offer.png")

    assert result["status"] == "SUCCESS"
    assert "guaranteed" in result["text"].lower()


def test_actual_providers_report_runtime_unavailability_without_fabrication():
    image_result = ocr.extract_text_from_image(make_png(), "image/png", "offer.png")
    if shutil.which("tesseract") is None:
        assert image_result["status"] == "PROVIDER_UNAVAILABLE"
        assert image_result["text"] is None

    audio_result = speech.transcribe_audio(make_wav(), "audio/wav", "voice.wav")
    if shutil.which("ffmpeg") is None:
        assert audio_result["status"] == "PROVIDER_UNAVAILABLE"
        assert audio_result["text"] is None
    else:
        try:
            import torch  # noqa: F401
            import whisper  # noqa: F401
        except ImportError:
            assert audio_result["status"] == "PROVIDER_UNAVAILABLE"
            assert audio_result["text"] is None


def test_text_normalization_and_language_detection():
    from app.services.normalization import normalize_extracted_text

    normalized, language = normalize_extracted_text("Pai\u0308sa\r\nguaranteed")
    assert normalized == "Païsa\nguaranteed"
    assert language == "EN"

    hindi_text, hindi_language = normalize_extracted_text("निवेश की जाँच करें")
    assert hindi_text == "निवेश की जाँच करें"
    assert hindi_language == "HI"


def test_real_whisper_transcription_when_configured():
    audio_path = os.environ.get("NIVESHSHAKTI_TEST_AUDIO")
    if not audio_path or not os.path.isfile(audio_path):
        pytest.skip("Real-provider check requires NIVESHSHAKTI_TEST_AUDIO with recorded speech.")
    if shutil.which("ffmpeg") is None:
        pytest.skip("Real-provider check requires FFmpeg.")
    try:
        import torch  # noqa: F401
        import whisper  # noqa: F401
    except ImportError:
        pytest.skip("Real-provider check requires PyTorch and openai-whisper.")

    suffix = os.path.splitext(audio_path)[1].lower()
    mime_type = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }.get(suffix)
    if mime_type is None:
        pytest.skip("Real Whisper fixture must use MP3, WAV, M4A, OGG, or FLAC.")

    result = speech.transcribe_audio(
        open(audio_path, "rb").read(), mime_type, os.path.basename(audio_path)
    )

    assert result["status"] == "SUCCESS"
    assert result["text"]
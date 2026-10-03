"""
Analysis router for NiveshShakti.
Endpoints:
- POST /analysis/text
- POST /analysis/url
- POST /analysis/image
- POST /analysis/audio
- GET /analysis/{id}
- GET /analysis/user/history
- GET /analysis/sources/health
"""
from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from urllib.parse import urlsplit

from ..database import get_db
from ..models import User, Analysis, AnalysisInput, AnalysisStatus, Source, Claim
from ..schemas import TextAnalysisRequest, URLAnalysisRequest, AnalysisDetailResponse, AnalysisSummaryResponse, SourceStatusResponse
from ..core.security import get_current_user
from ..services.pipeline import run_analysis_pipeline
from ..services.sources import ADAPTER_REGISTRY
from ..services.ocr import extract_text_from_image
from ..services.speech import transcribe_audio
from ..services.uploads import (
    AUDIO_MAX_FILE_SIZE_BYTES,
    AUDIO_UPLOAD_TYPES,
    IMAGE_MAX_FILE_SIZE_BYTES,
    IMAGE_UPLOAD_TYPES,
    UploadValidationError,
    read_limited_upload,
    validate_upload_metadata,
)

router = APIRouter()


async def _read_multimodal_upload(file: UploadFile, max_size: int, allowed_types: dict[str, set[str]]) -> bytes:
    try:
        validate_upload_metadata(file.filename, file.content_type, allowed_types)
        return await read_limited_upload(file, max_size)
    except UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def _record_analysis_input(
    db: Session,
    analysis: Analysis,
    media_type: str | None,
    byte_length: int,
    extraction_status: str | None = None,
) -> None:
    db.add(AnalysisInput(
        analysis_id=analysis.id,
        input_type=analysis.input_type,
        media_type=media_type,
        byte_length=byte_length,
        extraction_status=extraction_status,
    ))
    db.commit()

def validate_url_safety(url: str):
    """
    Reject malformed URLs and literal local/private targets before analysis.
    This endpoint does not fetch the submitted URL.
    """
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Malformed URL.") from exc

    if parsed.scheme.lower() not in {"http", "https"} or not host:
        raise HTTPException(status_code=400, detail="Invalid URL scheme. Must begin with http:// or https://")
    if parsed.username is not None or parsed.password is not None:
        raise HTTPException(status_code=400, detail="URLs containing embedded credentials are not accepted.")

    normalized_host = host.rstrip(".").lower()
    local_names = {"localhost", "metadata.google.internal", "metadata"}
    if normalized_host in local_names or normalized_host.endswith((".localhost", ".local", ".internal")):
        raise HTTPException(status_code=400, detail="Forbidden target host: local and metadata hosts are not accepted.")

    try:
        address = ipaddress.ip_address(normalized_host.split("%", 1)[0])
    except ValueError:
        address = None
        if re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|[0-9.]+)", normalized_host):
            try:
                address = ipaddress.ip_address(socket.inet_aton(normalized_host))
            except OSError as exc:
                raise HTTPException(status_code=400, detail="Malformed numeric host.") from exc

    if address is not None and not address.is_global:
        raise HTTPException(status_code=400, detail="Forbidden target host: non-public IP addresses are not accepted.")

@router.post("/text", response_model=AnalysisDetailResponse, status_code=status.HTTP_201_CREATED)
async def analyze_text_content(
    req: TextAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Initialize Analysis record
    analysis = Analysis(
        user_id=current_user.id,
        input_type="text",
        raw_input=req.text,
        status=AnalysisStatus.PENDING
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    _record_analysis_input(db, analysis, "text/plain; charset=utf-8", len(req.text.encode("utf-8")))

    # Run complete verification pipeline
    completed_analysis = await run_analysis_pipeline(analysis_id=analysis.id, text=req.text, db=db)
    
    # Reload with relationships
    return (
        db.query(Analysis)
        .options(
            joinedload(Analysis.claims).joinedload(Claim.verification_results),
            joinedload(Analysis.risk_indicators),
            joinedload(Analysis.entities)
        )
        .filter(Analysis.id == completed_analysis.id)
        .first()
    )

@router.post("/url", response_model=AnalysisDetailResponse, status_code=status.HTTP_201_CREATED)
async def analyze_url_content(
    req: URLAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    validate_url_safety(req.url)

    analysis = Analysis(
        user_id=current_user.id,
        input_type="url",
        raw_input=req.url,
        status=AnalysisStatus.PENDING
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    _record_analysis_input(db, analysis, "text/uri-list", len(req.url.encode("utf-8")))

    # Analyze URL text representation
    completed_analysis = await run_analysis_pipeline(
        analysis_id=analysis.id,
        text=f"Submitted financial URL (destination page not fetched): {req.url}",
        db=db
    )

    return (
        db.query(Analysis)
        .options(
            joinedload(Analysis.claims).joinedload(Claim.verification_results),
            joinedload(Analysis.risk_indicators),
            joinedload(Analysis.entities)
        )
        .filter(Analysis.id == completed_analysis.id)
        .first()
    )

@router.post("/image", response_model=AnalysisDetailResponse, status_code=status.HTTP_201_CREATED)
async def analyze_image_content(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an image upload, extract text via Tesseract OCR, then run the
    verification pipeline on the extracted text.

    If the Tesseract binary is not installed, returns a FAILED analysis with
    an honest PROVIDER_UNAVAILABLE message — no fabricated OCR output.
    """
    file_bytes = await _read_multimodal_upload(file, IMAGE_MAX_FILE_SIZE_BYTES, IMAGE_UPLOAD_TYPES)
    mime_type = file.content_type or ""

    ocr_result = extract_text_from_image(file_bytes, mime_type, file.filename or "")
    if ocr_result["status"] == "INVALID_INPUT":
        raise HTTPException(status_code=400, detail=ocr_result["message"])

    # Store the analysis record
    raw_input_label = "[image upload]"
    analysis = Analysis(
        user_id=current_user.id,
        input_type="image",
        raw_input=raw_input_label,
        extraction_status=ocr_result["status"],
        status=AnalysisStatus.PENDING
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    _record_analysis_input(db, analysis, mime_type, len(file_bytes), ocr_result["status"])

    if ocr_result["status"] != "SUCCESS":
        # Surface honest failure — do not feed None text into pipeline
        analysis.status = AnalysisStatus.FAILED
        analysis.extracted_text = None
        analysis.overall_risk_score = None
        analysis.overall_risk_level = None
        analysis.pause_recommendation = None
        analysis.explanation_beginner = ocr_result["message"]
        db.commit()
        db.refresh(analysis)
        return (
            db.query(Analysis)
            .options(
                joinedload(Analysis.claims).joinedload(Claim.verification_results),
                joinedload(Analysis.risk_indicators),
                joinedload(Analysis.entities)
            )
            .filter(Analysis.id == analysis.id)
            .first()
        )

    extracted_text = ocr_result["text"]
    analysis.extracted_text = extracted_text
    db.commit()

    if not extracted_text:
        # Image parsed but no text found — mark completed with empty result
        analysis.status = AnalysisStatus.COMPLETED
        analysis.detected_language = "UNKNOWN"
        analysis.explanation_beginner = "No text was detected in the uploaded image."
        db.commit()
        db.refresh(analysis)
        return (
            db.query(Analysis)
            .options(
                joinedload(Analysis.claims).joinedload(Claim.verification_results),
                joinedload(Analysis.risk_indicators),
                joinedload(Analysis.entities)
            )
            .filter(Analysis.id == analysis.id)
            .first()
        )

    completed_analysis = await run_analysis_pipeline(
        analysis_id=analysis.id, text=extracted_text, db=db
    )
    return (
        db.query(Analysis)
        .options(
            joinedload(Analysis.claims).joinedload(Claim.verification_results),
            joinedload(Analysis.risk_indicators),
            joinedload(Analysis.entities)
        )
        .filter(Analysis.id == completed_analysis.id)
        .first()
    )


@router.post("/audio", response_model=AnalysisDetailResponse, status_code=status.HTTP_201_CREATED)
async def analyze_audio_content(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an audio upload, transcribe via Whisper, then run the
    verification pipeline on the transcript.

    If PyTorch / Whisper are not installed, returns a FAILED analysis with
    an honest PROVIDER_UNAVAILABLE message — no fabricated transcript.
    """
    file_bytes = await _read_multimodal_upload(file, AUDIO_MAX_FILE_SIZE_BYTES, AUDIO_UPLOAD_TYPES)
    mime_type = file.content_type or ""
    filename = file.filename or "upload"

    speech_result = transcribe_audio(file_bytes, mime_type, filename)
    if speech_result["status"] == "INVALID_INPUT":
        raise HTTPException(status_code=400, detail=speech_result["message"])

    raw_input_label = "[audio upload]"
    analysis = Analysis(
        user_id=current_user.id,
        input_type="audio",
        raw_input=raw_input_label,
        extraction_status=speech_result["status"],
        status=AnalysisStatus.PENDING
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    _record_analysis_input(db, analysis, mime_type, len(file_bytes), speech_result["status"])

    if speech_result["status"] != "SUCCESS":
        analysis.status = AnalysisStatus.FAILED
        analysis.extracted_text = None
        analysis.overall_risk_score = None
        analysis.overall_risk_level = None
        analysis.pause_recommendation = None
        analysis.explanation_beginner = speech_result["message"]
        db.commit()
        db.refresh(analysis)
        return (
            db.query(Analysis)
            .options(
                joinedload(Analysis.claims).joinedload(Claim.verification_results),
                joinedload(Analysis.risk_indicators),
                joinedload(Analysis.entities)
            )
            .filter(Analysis.id == analysis.id)
            .first()
        )

    transcript = speech_result["text"]
    analysis.extracted_text = transcript
    db.commit()

    if not transcript:
        analysis.status = AnalysisStatus.COMPLETED
        analysis.detected_language = "UNKNOWN"
        analysis.explanation_beginner = "No speech was detected in the uploaded audio."
        db.commit()
        db.refresh(analysis)
        return (
            db.query(Analysis)
            .options(
                joinedload(Analysis.claims).joinedload(Claim.verification_results),
                joinedload(Analysis.risk_indicators),
                joinedload(Analysis.entities)
            )
            .filter(Analysis.id == analysis.id)
            .first()
        )

    completed_analysis = await run_analysis_pipeline(
        analysis_id=analysis.id, text=transcript, db=db
    )
    return (
        db.query(Analysis)
        .options(
            joinedload(Analysis.claims).joinedload(Claim.verification_results),
            joinedload(Analysis.risk_indicators),
            joinedload(Analysis.entities)
        )
        .filter(Analysis.id == completed_analysis.id)
        .first()
    )



@router.get("/user/history", response_model=List[AnalysisSummaryResponse])
def get_user_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    results = []
    for item in analyses:
        results.append(AnalysisSummaryResponse(
            id=item.id,
            input_type=item.input_type,
            raw_input=item.raw_input[:100] + ("..." if len(item.raw_input) > 100 else ""),
            status=item.status,
            overall_risk_score=item.overall_risk_score,
            overall_risk_level=item.overall_risk_level,
            pause_recommendation=item.pause_recommendation,
            explanation=item.explanation_beginner,
            created_at=item.created_at,
            risk_indicators_count=len(item.risk_indicators),
            claims_count=len(item.claims)
        ))
    return results

@router.get("/sources/health", response_model=List[SourceStatusResponse])
async def get_source_health_statuses(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    adapter_items = list(ADAPTER_REGISTRY.items())
    retrievals = await asyncio.gather(*(adapter.retrieve() for _, adapter in adapter_items))
    for (code, adapter), retrieval in zip(adapter_items, retrievals):
        db_s = next((s for s in sources if s.code == code), None)
        checked_at = datetime.utcnow()
        if not db_s:
            db_s = Source(
                code=code,
                name=adapter.name,
                url=adapter.manual_url,
                source_type=adapter.source_type,
                health_status=retrieval["health_status"],
                last_checked_at=checked_at,
                last_successful_retrieval_at=checked_at if retrieval["retrieval_status"] == "AVAILABLE" else None,
                last_retrieval_status=retrieval["retrieval_status"],
                last_error=retrieval["last_error"],
            )
            db.add(db_s)
        else:
            db_s.name = adapter.name
            db_s.url = adapter.manual_url
            db_s.source_type = adapter.source_type
            db_s.health_status = retrieval["health_status"]
            db_s.last_checked_at = checked_at
            db_s.last_retrieval_status = retrieval["retrieval_status"]
            db_s.last_error = retrieval["last_error"]
            if retrieval["retrieval_status"] == "AVAILABLE":
                db_s.last_successful_retrieval_at = checked_at
    db.commit()
    return db.query(Source).all()

@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis_detail(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analysis = (
        db.query(Analysis)
        .options(
            joinedload(Analysis.claims).joinedload(Claim.verification_results),
            joinedload(Analysis.risk_indicators),
            joinedload(Analysis.entities)
        )
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis report not found")
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis report not found")
    db.delete(analysis)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""
SQLAlchemy models for NiveshShakti.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from .database import Base
import enum

class KnowledgeLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class Language(str, enum.Enum):
    EN = "EN"
    HI = "HI"
    HINGLISH = "HINGLISH"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    language = Column(Enum(Language), default=Language.EN)
    knowledge_level = Column(Enum(KnowledgeLevel), default=KnowledgeLevel.BEGINNER)

    analyses = relationship("Analysis", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class VerificationStatus(str, enum.Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    input_type = Column(String, nullable=False)  # text, image, url, audio
    raw_input = Column(Text, nullable=False)
    extracted_text = Column(Text, nullable=True)
    extraction_status = Column(String, nullable=True)
    detected_language = Column(String, nullable=True)
    content_classification = Column(String, nullable=True)
    content_signals = Column(JSON, nullable=True)
    overall_risk_score = Column(Float, default=0.0)  # 0 to 100
    overall_risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    pause_recommendation = Column(Text, nullable=True)
    explanation_beginner = Column(Text, nullable=True)
    explanation_intermediate = Column(Text, nullable=True)
    explanation_advanced = Column(Text, nullable=True)
    explanation_hindi = Column(Text, nullable=True)
    explanation_hindi_intermediate = Column(Text, nullable=True)
    explanation_hindi_advanced = Column(Text, nullable=True)
    explanation_hinglish = Column(Text, nullable=True)
    explanation_hinglish_intermediate = Column(Text, nullable=True)
    explanation_hinglish_advanced = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="analyses")
    claims = relationship("Claim", back_populates="analysis", cascade="all, delete-orphan")
    risk_indicators = relationship("RiskIndicator", back_populates="analysis", cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="analysis", cascade="all, delete-orphan")
    inputs = relationship("AnalysisInput", back_populates="analysis", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisInput(Base):
    __tablename__ = "analysis_inputs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    input_type = Column(String, nullable=False)
    media_type = Column(String, nullable=True)
    byte_length = Column(Integer, nullable=True)
    extraction_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="inputs")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String, nullable=True)  # e.g., "guaranteed_return", "registration", "urgency", "price_target"
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="claims")
    verification_results = relationship("VerificationResult", back_populates="claim", cascade="all, delete-orphan")

class RiskIndicator(Base):
    __tablename__ = "risk_indicators"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    indicator_code = Column(String, nullable=False)  # e.g. "GUARANTEED_RETURNS_PROMISE", "UNREGISTERED_INTERMEDIARY"
    title = Column(String, nullable=False)
    severity = Column(Enum(RiskLevel), nullable=False)
    evidence_snippet = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="risk_indicators")

class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    entity_text = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)  # REG_NUMBER, COMPANY, PERSON, PERCENTAGE_RETURN, PHONE, URL, UPI_ID
    normalized_value = Column(String, nullable=True)

    analysis = relationship("Analysis", back_populates="entities")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False) # e.g. "SEBI_INTERMEDIARIES", "RBI_Sachet"
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source_type = Column(String, default="authoritative")  # authoritative, regulatory
    is_active = Column(Boolean, default=True)
    health_status = Column(String, default="UNKNOWN")  # UNKNOWN, AVAILABLE, DEGRADED, UNAVAILABLE
    last_checked_at = Column(DateTime, default=datetime.utcnow)
    last_successful_retrieval_at = Column(DateTime, nullable=True)
    last_retrieval_status = Column(String, nullable=True)
    last_error = Column(String, nullable=True)

    verification_results = relationship("VerificationResult", back_populates="source")

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    source_name = Column(String, nullable=True)
    source_code = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.SOURCE_UNAVAILABLE)
    retrieval_status = Column(String, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    source_published_at = Column(DateTime, nullable=True)
    source_version = Column(String, nullable=True)
    query_used = Column(String, nullable=True)
    evidence_text = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)

    claim = relationship("Claim", back_populates="verification_results")
    source = relationship("Source", back_populates="verification_results")
    evidence_item = relationship("EvidenceItem", back_populates="verification_result", uselist=False)


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    verification_result_id = Column(Integer, ForeignKey("verification_results.id"), unique=True, nullable=False)
    source_name = Column(String, nullable=False)
    source_code = Column(String, nullable=False)
    source_type = Column(String, nullable=True)
    status = Column(Enum(VerificationStatus), nullable=False)
    retrieval_status = Column(String, nullable=True)
    evidence_text = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    source_published_at = Column(DateTime, nullable=True)
    source_version = Column(String, nullable=True)

    analysis = relationship("Analysis", back_populates="evidence_items")
    verification_result = relationship("VerificationResult", back_populates="evidence_item")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class LearningContent(Base):
    __tablename__ = "learning_content"

    id = Column(Integer, primary_key=True, index=True)
    content_code = Column(String, unique=True, nullable=False)
    language = Column(String, nullable=False)
    knowledge_level = Column(String, nullable=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    source_published_at = Column(DateTime, nullable=True)
    source_version = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GrievanceGuidance(Base):
    __tablename__ = "grievance_guidance"

    id = Column(Integer, primary_key=True, index=True)
    guidance_code = Column(String, unique=True, nullable=False)
    language = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    source_published_at = Column(DateTime, nullable=True)
    source_version = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

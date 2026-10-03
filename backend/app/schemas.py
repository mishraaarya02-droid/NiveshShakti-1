"""
Pydantic schemas for NiveshShakti API requests and responses.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .models import Language, KnowledgeLevel, AnalysisStatus, VerificationStatus, RiskLevel

# Auth Schemas
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    language: Language = Language.EN
    knowledge_level: KnowledgeLevel = KnowledgeLevel.BEGINNER

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPreferencesUpdateRequest(BaseModel):
    language: Language
    knowledge_level: KnowledgeLevel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserProfileResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    language: Language
    knowledge_level: KnowledgeLevel
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Verification & Claim Schemas
class VerificationResultSchema(BaseModel):
    id: int
    source_name: str
    source_code: str
    source_type: Optional[str] = None
    status: VerificationStatus
    retrieval_status: Optional[str] = None
    evidence_text: Optional[str]
    retrieved_at: datetime
    source_published_at: Optional[datetime] = None
    source_version: Optional[str] = None
    source_url: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ClaimSchema(BaseModel):
    id: int
    claim_text: str
    claim_type: Optional[str]
    verification_status: VerificationStatus
    explanation: Optional[str]
    verification_results: List[VerificationResultSchema] = []

    model_config = ConfigDict(from_attributes=True)

class RiskIndicatorSchema(BaseModel):
    id: int
    indicator_code: str
    title: str
    severity: RiskLevel
    evidence_snippet: Optional[str]
    description: str

    model_config = ConfigDict(from_attributes=True)

class ExtractedEntitySchema(BaseModel):
    id: int
    entity_text: str
    entity_type: str
    normalized_value: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# Analysis Request & Response Schemas
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Financial claim or message content to verify")
    language: Optional[Language] = None
    knowledge_level: Optional[KnowledgeLevel] = None

class URLAnalysisRequest(BaseModel):
    url: str = Field(..., description="Financial investment URL or website to verify")

class AnalysisSummaryResponse(BaseModel):
    id: int
    input_type: str
    raw_input: str
    status: AnalysisStatus
    overall_risk_score: Optional[float]
    overall_risk_level: Optional[RiskLevel]
    pause_recommendation: Optional[str]
    explanation: Optional[str]
    created_at: datetime
    risk_indicators_count: int
    claims_count: int

    model_config = ConfigDict(from_attributes=True)

class AnalysisDetailResponse(BaseModel):
    id: int
    input_type: str
    raw_input: str
    extracted_text: Optional[str]
    extraction_status: Optional[str]
    detected_language: Optional[str]
    content_classification: Optional[str] = None
    content_signals: Optional[list[dict]] = None
    status: AnalysisStatus
    overall_risk_score: Optional[float]
    overall_risk_level: Optional[RiskLevel]
    pause_recommendation: Optional[str]
    explanation_beginner: Optional[str]
    explanation_intermediate: Optional[str]
    explanation_advanced: Optional[str]
    explanation_hindi: Optional[str]
    explanation_hindi_intermediate: Optional[str] = None
    explanation_hindi_advanced: Optional[str] = None
    explanation_hinglish: Optional[str] = None
    explanation_hinglish_intermediate: Optional[str] = None
    explanation_hinglish_advanced: Optional[str] = None
    created_at: datetime
    claims: List[ClaimSchema] = []
    risk_indicators: List[RiskIndicatorSchema] = []
    entities: List[ExtractedEntitySchema] = []

    model_config = ConfigDict(from_attributes=True)

# Source Status Schema
class SourceStatusResponse(BaseModel):
    id: int
    code: str
    name: str
    url: str
    source_type: str
    is_active: bool
    health_status: str
    last_checked_at: datetime
    last_successful_retrieval_at: Optional[datetime] = None
    last_retrieval_status: Optional[str] = None
    last_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GrievanceChannel(BaseModel):
    name: str
    url: str
    description: str
    is_official: bool = True


class GrievanceSituation(BaseModel):
    id: str
    title: str
    title_hindi: str
    description: str
    description_hindi: str
    immediate_actions: List[str]
    evidence_to_preserve: List[str]
    required_information: List[str]
    official_channels: List[GrievanceChannel]
    important_note: str

/**
 * Shared TypeScript types for NiveshShakti frontend.
 */

export interface UserProfile {
  id: number;
  email: string;
  is_active: boolean;
  language: 'EN' | 'HI' | 'HINGLISH';
  knowledge_level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  created_at: string;
}

export interface RiskIndicator {
  id: number;
  indicator_code: string;
  title: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  evidence_snippet?: string;
  description: string;
}

export interface VerificationResult {
  id: number;
  source_name: string;
  source_code: string;
  source_type?: string;
  status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNVERIFIED' | 'UNSUPPORTED' | 'CONTRADICTED' | 'SOURCE_UNAVAILABLE';
  retrieval_status?: string;
  evidence_text?: string;
  retrieved_at: string;
  source_published_at?: string | null;
  source_version?: string | null;
  source_url?: string;
}

export interface Claim {
  id: number;
  claim_text: string;
  claim_type?: string;
  verification_status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNVERIFIED' | 'UNSUPPORTED' | 'CONTRADICTED' | 'SOURCE_UNAVAILABLE';
  explanation?: string;
  verification_results: VerificationResult[];
}

export interface ExtractedEntity {
  id: number;
  entity_text: string;
  entity_type: string;
  normalized_value?: string;
}

export interface AnalysisDetail {
  id: number;
  input_type: string;
  raw_input: string;
  extracted_text?: string;
  extraction_status?: 'SUCCESS' | 'PROVIDER_UNAVAILABLE' | 'INVALID_INPUT' | 'ERROR';
  detected_language?: 'EN' | 'HI' | 'HINGLISH' | 'UNKNOWN';
  content_classification?: 'PROMOTIONAL_CUES' | 'EDUCATIONAL_CUES' | 'MIXED_CUES' | 'UNCLEAR' | null;
  content_signals?: { code: string; description: string; matched_text: string }[] | null;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  overall_risk_score: number | null;
  overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null;
  pause_recommendation?: string;
  explanation_beginner?: string;
  explanation_intermediate?: string;
  explanation_advanced?: string;
  explanation_hindi?: string;
  explanation_hindi_intermediate?: string;
  explanation_hindi_advanced?: string;
  explanation_hinglish?: string;
  explanation_hinglish_intermediate?: string;
  explanation_hinglish_advanced?: string;
  created_at: string;
  claims: Claim[];
  risk_indicators: RiskIndicator[];
  entities: ExtractedEntity[];
}

export interface AnalysisSummary {
  id: number;
  input_type: string;
  raw_input: string;
  status: string;
  overall_risk_score: number | null;
  overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null;
  pause_recommendation?: string;
  explanation?: string;
  created_at: string;
  risk_indicators_count: number;
  claims_count: number;
}

export interface SourceHealth {
  id: number;
  code: string;
  name: string;
  url: string;
  health_status: 'UNKNOWN' | 'AVAILABLE' | 'DEGRADED' | 'UNAVAILABLE';
  last_checked_at: string;
  last_successful_retrieval_at?: string | null;
  last_retrieval_status?: string | null;
  last_error?: string | null;
}

export interface GrievanceChannel {
  name: string;
  url: string;
  description: string;
  is_official: boolean;
}

export interface GrievanceSituation {
  id: string;
  title: string;
  title_hindi: string;
  description: string;
  description_hindi: string;
  immediate_actions: string[];
  evidence_to_preserve: string[];
  required_information: string[];
  official_channels: GrievanceChannel[];
  important_note: string;
}

/**
 * Typed API Client for NiveshShakti Backend.
 * Handles JWT tokens, authentication, submissions, and result fetching.
 */
export type {
  UserProfile,
  AnalysisDetail,
  AnalysisSummary,
  SourceHealth,
  RiskIndicator,
  VerificationResult,
  Claim,
  ExtractedEntity,
  GrievanceSituation,
  GrievanceChannel,
} from './types';

import type { UserProfile, AnalysisDetail, AnalysisSummary, SourceHealth, GrievanceSituation } from './types';

const API_BASE = '';

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function readErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const error: { detail?: unknown } = await res.json();
    if (typeof error.detail === 'string') return error.detail;
    if (Array.isArray(error.detail)) {
      return error.detail
        .map((item) => typeof item === 'object' && item !== null && 'msg' in item ? String(item.msg) : '')
        .filter(Boolean)
        .join('; ') || fallback;
    }
  } catch {
    // Some proxies and server errors return an empty or non-JSON body.
  }
  return fallback;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = api.getToken();
  const headers: Record<string, string> = {};

  // Only set Content-Type for JSON bodies; FormData sets its own boundary
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (options.headers) {
    Object.assign(headers, options.headers as Record<string, string>);
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  } catch {
    throw new ApiError('Unable to reach the backend. Check that the API is running and try again.', 0);
  }

  if (!res.ok) {
    const fallback = res.status >= 500
      ? `The backend returned HTTP ${res.status}. Check that the API is running and try again.`
      : res.statusText || 'API request failed';
    throw new ApiError(await readErrorMessage(res, fallback), res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function uploadFile<T>(endpoint: string, file: File): Promise<T> {
  const token = api.getToken();
  const formData = new FormData();
  formData.append('file', file);
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });
  } catch {
    throw new ApiError('Unable to reach the backend. Check that the API is running and try again.', 0);
  }
  if (!res.ok) {
    const fallback = res.status >= 500
      ? `The backend returned HTTP ${res.status}. Check that the API is running and try again.`
      : res.statusText || 'Upload failed';
    throw new ApiError(await readErrorMessage(res, fallback), res.status);
  }
  return res.json();
}

export const api = {
  getToken: () => localStorage.getItem('ns_access_token'),
  setToken: (token: string) => localStorage.setItem('ns_access_token', token),
  clearToken: () => localStorage.removeItem('ns_access_token'),

  // Auth
  register: (data: { email: string; password: string; language?: string; knowledge_level?: string }) =>
    request<UserProfile>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getProfile: () => request<UserProfile>('/auth/me'),

  updatePreferences: (language: UserProfile['language'], knowledge_level: UserProfile['knowledge_level']) =>
    request<UserProfile>('/auth/me/preferences', {
      method: 'PATCH',
      body: JSON.stringify({ language, knowledge_level }),
    }),

  // Analysis
  analyzeText: (text: string) =>
    request<AnalysisDetail>('/analysis/text', { method: 'POST', body: JSON.stringify({ text }) }),

  analyzeUrl: (url: string) =>
    request<AnalysisDetail>('/analysis/url', { method: 'POST', body: JSON.stringify({ url }) }),

  analyzeImage: (file: File) => uploadFile<AnalysisDetail>('/analysis/image', file),

  analyzeAudio: (file: File) => uploadFile<AnalysisDetail>('/analysis/audio', file),

  getHistory: () => request<AnalysisSummary[]>('/analysis/user/history'),

  getDetail: (id: number) => request<AnalysisDetail>(`/analysis/${id}`),

  deleteAnalysis: (id: number) => request<void>(`/analysis/${id}`, { method: 'DELETE' }),

  getSourceHealth: () => request<SourceHealth[]>('/analysis/sources/health'),

  // Grievance
  getGrievanceSituations: () => request<GrievanceSituation[]>('/grievance/situations'),
};

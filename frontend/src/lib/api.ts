import { getAccessToken } from "./auth";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "https://prism-backend-pixj.onrender.com")
  .replace(/\/+$/, "")
  .replace(/\/api$/, "");

export interface Analysis {
  id: string;
  user_id: string;
  organization_id: string | null;
  query_text: string | null;
  status: string;
  detected_language: string | null;
  product_name: string | null;
  product_category_id: string | null;
  error_message?: string | null;
}

export interface Standard {
  id: string;
  standard_number: string;
  title: string;
  description: string | null;
  scope: string | null;
  product_category_id: string | null;
  technical_domain: string | null;
  status: string;
  source_name: string | null;
  source_url: string | null;
}

export interface StandardVersion {
  id: string;
  standard_id: string;
  version_label?: string | null;
  publication_date?: string | null;
  is_current?: boolean | null;
  source_url?: string | null;
}

export interface Recommendation {
  id: string;
  analysis_id: string;
  standard_id: string;
  standard_version_id: string | null;
  recommendation_type: string;
  rank: number;
  relevance_score: number;
  confidence_score: number;
  explanation: string | null;
  review_status: string;
  standard?: Standard | null;
  standard_version?: StandardVersion | null;
  evidence: Evidence[];
  reviews?: Review[];
  feedback?: Feedback[];
}

export interface Evidence {
  id?: string;
  recommendation_id?: string;
  evidence_type: string;
  evidence_text: string;
  source_standard_id?: string | null;
  source_url?: string | null;
}

export interface Review {
  id: string;
  recommendation_id: string;
  reviewer_id: string;
  status: string;
  comments: string | null;
  reviewed_at?: string | null;
}

export interface Feedback {
  id: string;
  recommendation_id: string;
  user_id: string;
  feedback_type: string;
  comments: string | null;
}

export interface Report {
  analysis: Analysis;
  requirements: Requirement[];
  recommendations: Recommendation[];
  documents: UploadedDocument[];
}

export interface UploadedDocument {
  id: string;
  analysis_id: string;
  file_name: string;
  mime_type: string | null;
  file_size?: number | null;
  status: string;
  extracted_text?: string | null;
  ocr_used?: boolean | null;
  processing_error?: string | null;
}

export interface Requirement {
  id?: string;
  requirement_type: string;
  requirement_text: string;
  normalized_value?: string | null;
}

export interface CertificationRequirement {
  id?: string;
  certification_name?: string | null;
  scheme_type?: string | null;
  description?: string | null;
  mandatory?: boolean | null;
  source?: string | null;
  source_url?: string | null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error(`API request failed: ${options.method ?? "GET"} ${path} - Network error`);
  }
  if (!response.ok) {
    const body = await response.text();
    let detail = "";
    try {
      detail = (JSON.parse(body) as { detail?: string }).detail ?? "";
    } catch {
      detail = body.trim();
    }
    if (response.status === 403) {
      throw new Error(`You do not have permission to perform this action${detail ? `: ${detail}` : "."}`);
    }
    throw new Error(`API request failed: ${options.method ?? "GET"} ${path} - ${response.status} ${response.statusText}${detail ? `: ${detail}` : ""}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  listAnalyses: () => request<Analysis[]>("/api/analyses"),
  getAnalysis: (id: string) => request<Analysis>(`/api/analyses/${id}`),
  createAnalysis: (payload: { query_text: string; product_name?: string; technical_specifications?: string; defer_processing?: boolean }) =>
    request<Analysis>("/api/analyses", { method: "POST", body: JSON.stringify(payload) }),
  getReport: (id: string) => request<Report>(`/api/analyses/${id}/report`),
  searchStandards: (query = "") =>
    request<Standard[]>(`/api/standards/search?search=${encodeURIComponent(query)}&limit=100`),
  getStandard: (id: string) => request<Standard>(`/api/standards/${id}`),
  getVersions: (id: string) => request<StandardVersion[]>(`/api/standards/${id}/versions`),
  getAmendments: (id: string) => request<Record<string, unknown>[]>(`/api/standards/${id}/amendments`),
  getRelationships: (id: string) => request<Record<string, unknown>[]>(`/api/standards/${id}/relationships`),
  getCertification: (id: string) => request<CertificationRequirement[]>(`/api/standards/${id}/certification`),
  uploadDocument: async (analysisId: string, file: File) => {
    const token = await getAccessToken();
    const form = new FormData();
    form.append("file", file);
    let response: Response;
    try {
      response = await fetch(`${API_URL}/api/analyses/${analysisId}/documents`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
    } catch {
      throw new Error("API request failed: POST /api/analyses/{id}/documents - Network error");
    }
    if (!response.ok) {
      const body = await response.text();
      let detail = "";
      try {
        detail = (JSON.parse(body) as { detail?: string }).detail ?? "";
      } catch {
        detail = body.trim();
      }
      throw new Error(
        `API request failed: POST /api/analyses/{id}/documents - ${response.status} ${response.statusText}${detail ? `: ${detail}` : ""}`,
      );
    }
    return response.json();
  },
  review: (id: string, status: string, comments: string) =>
    request<Review>(`/api/recommendations/${id}/review`, { method: "POST", body: JSON.stringify({ status, comments }) }),
  feedback: (id: string, feedback_type: string, comments: string) =>
    request<Feedback>(`/api/recommendations/${id}/feedback`, { method: "POST", body: JSON.stringify({ feedback_type, comments }) }),
  listReviews: (id: string) => request<Review[]>(`/api/recommendations/${id}/reviews`),
  listAdminUsers: () => request<Record<string, unknown>[]>("/api/admin/users"),
  listAdminStandards: () => request<Standard[]>("/api/admin/standards"),
};

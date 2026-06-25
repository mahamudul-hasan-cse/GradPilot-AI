import type { PaginatedResponse, Scholarship, TokenResponse, University, User } from "@gradpilot/shared";

import { getApiV1Url } from "./utils";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  formData?: FormData;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};

  if (!options.formData) {
    headers["Content-Type"] = "application/json";
  }

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(`${getApiV1Url()}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.formData ?? (options.body ? JSON.stringify(options.body) : undefined),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message =
      typeof errorBody.detail === "string"
        ? errorBody.detail
        : `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ── Response types ──────────────────────────────────────────────────────────

export type StudentProfile = {
  id: string;
  user_id: string;
  nationality: string | null;
  target_countries: string[] | null;
  target_degree: string | null;
  field_of_study: string | null;
  gpa: number | null;
  ielts_score: number | null;
  toefl_score: number | null;
  gre_score: number | null;
  budget_max: number | null;
  bio: string | null;
};

export type ProfileAnalysis = {
  readiness_score: number;
  academic_score: number;
  language_score: number;
  experience_score: number;
  recommendations: string[];
  strengths: string[];
  gaps: string[];
};

export type UniversityRecommendation = {
  university_id: string;
  university_name: string;
  country: string;
  match_score: number;
  reasons: string[];
};

export type ScholarshipRecommendation = {
  scholarship_id: string;
  title: string;
  match_score: number;
  reasons: string[];
};

export type ApplicationItem = {
  id: string;
  user_id: string;
  status: string;
  university_id: string | null;
  program_id: string | null;
  notes: string | null;
  deadline: string | null;
  created_at: string;
  updated_at: string;
};

export type ApplicationWorkspace = {
  application: ApplicationItem;
  progress_percent: number;
  tasks: Array<{ id: string; title: string; status: string; due_date: string | null }>;
  deadlines: Array<{ id: string; title: string; due_date: string; is_completed: boolean }>;
  documents: Array<{ id: string; title: string; document_type: string; status: string }>;
};

export type DocumentUpload = {
  id: string;
  document_type: string | null;
  file_name: string;
  status: string;
  classified_type: string | null;
  extracted_fields: Record<string, unknown> | null;
  confidence_score: number | null;
  validation_result: { is_valid: boolean; errors: string[] } | null;
  created_at: string;
};

export type DigitalTwin = {
  profile: Record<string, unknown>;
  readiness: Record<string, unknown>;
  documents: unknown[];
  applications: unknown[];
  recommendations: Record<string, unknown>;
  last_refreshed_at: string | null;
};

export type TimelineEntry = {
  id: string;
  event_type: string;
  title: string;
  description: string | null;
  occurred_at: string;
  metadata: Record<string, unknown> | null;
};

export type ChatMessage = { role: string; content: string };

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<TokenResponse>("/auth/login", { method: "POST", body: { email, password } }),
    register: (email: string, password: string, full_name: string) =>
      request<User>("/auth/register", { method: "POST", body: { email, password, full_name } }),
    me: (token: string) => request<User>("/auth/me", { token }),
    refresh: (refresh_token: string) =>
      request<TokenResponse>("/auth/refresh", { method: "POST", body: { refresh_token } }),
  },

  profile: {
    get: (token: string) => request<StudentProfile>("/profile", { token }),
    update: (token: string, data: Partial<StudentProfile>) =>
      request<StudentProfile>("/profile", { method: "PUT", body: data, token }),
    analyze: (token: string) =>
      request<ProfileAnalysis>("/profile/analyze", { method: "POST", token }),
  },

  universities: {
    list: (params?: { country?: string; q?: string; skip?: number; limit?: number }) => {
      const search = new URLSearchParams();
      if (params?.country) search.set("country", params.country);
      if (params?.q) search.set("q", params.q);
      if (params?.skip !== undefined) search.set("skip", String(params.skip));
      if (params?.limit !== undefined) search.set("limit", String(params.limit));
      const query = search.toString();
      return request<PaginatedResponse<University>>(`/universities${query ? `?${query}` : ""}`);
    },
    get: (id: string) => request<University>(`/universities/${id}`),
    search: (body: { query?: string; country?: string; skip?: number; limit?: number }) =>
      request<PaginatedResponse<University>>("/universities/search", { method: "POST", body }),
  },

  scholarships: {
    list: (params?: { country?: string; q?: string; skip?: number; limit?: number }) => {
      const search = new URLSearchParams();
      if (params?.country) search.set("country", params.country);
      if (params?.q) search.set("q", params.q);
      if (params?.skip !== undefined) search.set("skip", String(params.skip));
      if (params?.limit !== undefined) search.set("limit", String(params.limit));
      const query = search.toString();
      return request<PaginatedResponse<Scholarship>>(`/scholarships${query ? `?${query}` : ""}`);
    },
    get: (id: string) => request<Scholarship>(`/scholarships/${id}`),
  },

  recommendations: {
    universities: (token: string, body?: { limit?: number }) =>
      request<{ recommendations: UniversityRecommendation[] }>("/recommendations/universities", {
        method: "POST",
        body: body ?? {},
        token,
      }),
    scholarships: (token: string, body?: { limit?: number }) =>
      request<{ recommendations: ScholarshipRecommendation[] }>("/recommendations/scholarships", {
        method: "POST",
        body: body ?? {},
        token,
      }),
  },

  applications: {
    list: (token: string) => request<ApplicationItem[]>("/applications", { token }),
    get: (token: string, id: string) => request<ApplicationItem>(`/applications/${id}`, { token }),
    workspace: (token: string, id: string) =>
      request<ApplicationWorkspace>(`/applications/${id}/workspace`, { token }),
    create: (token: string, data: { university_id?: string; notes?: string }) =>
      request<ApplicationItem>("/applications", { method: "POST", body: data, token }),
    progress: (token: string, id: string) =>
      request<{ progress_percent: number }>(`/applications/${id}/progress`, { token }),
  },

  documents: {
    list: (token: string) => request<DocumentUpload[]>("/documents", { token }),
    get: (token: string, id: string) => request<DocumentUpload>(`/documents/${id}`, { token }),
    upload: (token: string, file: File, documentType?: string) => {
      const formData = new FormData();
      formData.append("file", file);
      if (documentType) formData.append("document_type", documentType);
      return request<DocumentUpload>("/documents/upload", { method: "POST", formData, token });
    },
    parse: (token: string, id: string) =>
      request<DocumentUpload>(`/documents/${id}/parse`, { method: "POST", token }),
  },

  student: {
    digitalTwin: (token: string) =>
      request<DigitalTwin>("/student/digital-twin", { token }),
    timeline: (token: string) =>
      request<{ entries: TimelineEntry[] }>("/student/timeline", { token }),
    refresh: (token: string) =>
      request<{ message: string }>("/student/refresh", { method: "POST", token }),
  },

  ai: {
    chat: (token: string, message: string, sessionId?: string) =>
      request<{ response: string; session_id: string }>("/ai/chat", {
        method: "POST",
        body: { message, session_id: sessionId },
        token,
      }),
    search: (token: string, query: string) =>
      request<{ results: Array<{ title: string; content: string; score: number }> }>("/ai/search", {
        method: "POST",
        body: { query },
        token,
      }),
  },
};

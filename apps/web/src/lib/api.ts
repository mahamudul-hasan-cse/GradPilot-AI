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
    if (response.status === 401 && typeof window !== "undefined") {
      const callbackUrl = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.assign(`/login?callbackUrl=${callbackUrl}`);
    }
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
  current_country: string | null;
  education_level: string | null;
  target_countries: string[] | null;
  target_degree: string | null;
  field_of_study: string | null;
  gpa: number | null;
  gpa_scale: number | null;
  test_scores: Record<string, number | string | null> | null;
  work_experience_years: number | null;
  budget_min: number | null;
  budget_max: number | null;
  budget_currency: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
};

export type ProfileAnalysis = {
  admission_readiness_score: number;
  scholarship_readiness_score: number;
  employability_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_requirements: string[];
  recommended_actions: string[];
  recommended_countries: string[];
  recommended_university_tier: string;
  profile_summary: string;
  score_explanations: Record<string, { score: number; label: string; explanation: string; factors: Record<string, number> }>;
};

export type ProfileAnalysisRequest = {
  cgpa: number;
  ielts: number;
  degree_level: string;
  major: string;
  country_preferences?: string[];
  work_experience_years?: number;
  has_research_experience?: boolean;
  publications_count?: number;
  certifications?: string[];
  use_cache?: boolean;
};

export type UniversityRecommendationRequest = {
  cgpa: number;
  ielts: number;
  budget: number;
  country_preference?: string | null;
  major: string;
  work_experience_years?: number;
  has_research_experience?: boolean;
  limit_per_tier?: number;
  use_cache?: boolean;
};

export type RecommendedUniversity = {
  university: University;
  score_breakdown: {
    academic_match: number;
    language_match: number;
    budget_match: number;
    program_match: number;
    scholarship_match: number;
    recommendation_score: number;
    tier: "safe" | "target" | "ambitious";
  };
  explanation: string;
};

export type UniversityRecommendationResponse = {
  recommendations: {
    safe: RecommendedUniversity[];
    target: RecommendedUniversity[];
    ambitious: RecommendedUniversity[];
  };
  total_candidates_evaluated: number;
};

export type ScholarshipRecommendationRequest = {
  cgpa: number;
  ielts: number;
  degree_level: string;
  major: string;
  country_preference?: string | null;
  has_research_experience?: boolean;
  work_experience_years?: number;
  nationality?: string | null;
  min_score?: number;
  limit?: number;
  use_cache?: boolean;
};

export type MatchedScholarship = {
  scholarship: Scholarship;
  score: {
    academic_match: number;
    language_match: number;
    degree_match: number;
    country_match: number;
    research_match: number;
    work_experience_match: number;
    scholarship_score: number;
    eligibility_probability: number;
    match_category: string;
  };
  explanation: string;
};

export type ScholarshipRecommendationResponse = {
  matches: MatchedScholarship[];
  total_candidates_evaluated: number;
};

export type ApplicationItem = {
  id: string;
  user_id: string;
  status: string;
  university_id: string | null;
  program_id: string | null;
  notes: string | null;
  deadline: string | null;
  title?: string | null;
  progress_percent?: number;
  university?: University | null;
  created_at: string;
  updated_at: string;
};

export type ApplicationWorkspace = {
  application: ApplicationItem;
  progress: { progress_percent: number; breakdown: Record<string, unknown> };
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
  event_type?: string;
  category?: string;
  title: string;
  description: string | null;
  occurred_at: string;
  metadata: Record<string, unknown> | null;
};

export type ChatMessage = { role: string; content: string };
export type ChatResponse = { answer: string; session_id: string | null; confidence: number; model: string };

export type PlannerTask = {
  id: string;
  title: string;
  description: string | null;
  category: string;
  task_type: string;
  reason: string;
  priority_score: number;
  priority_rank: number | null;
  status: string;
  due_date: string | null;
  scheduled_date: string | null;
};

export type PlannerPlan = {
  plan_id: string;
  priority_score: number;
  todays_tasks: PlannerTask[];
  tomorrows_tasks: PlannerTask[];
  weekly_goals: Array<{ title: string; description: string | null; reason: string; due_date: string | null }>;
  risk_alerts: Array<{ title: string; description: string | null; reason: string }>;
  deadline_alerts: Array<{ title: string; description: string | null; reason: string }>;
  generated_at: string;
};

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
    get: async (token: string) => {
      try {
        return await request<StudentProfile>("/profile", { token });
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    update: (token: string, data: Partial<StudentProfile>) =>
      request<StudentProfile>("/profile", { method: "PUT", body: data, token }),
    analyze: (token: string, data: ProfileAnalysisRequest) =>
      request<ProfileAnalysis>("/profile/analyze", { method: "POST", body: data, token }),
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
    universities: (token: string, body: UniversityRecommendationRequest) =>
      request<UniversityRecommendationResponse>("/recommendations/universities", {
        method: "POST",
        body,
        token,
      }),
    scholarships: (token: string, body: ScholarshipRecommendationRequest) =>
      request<ScholarshipRecommendationResponse>("/recommendations/scholarships", {
        method: "POST",
        body,
        token,
      }),
  },

  applications: {
    list: (token: string) => request<ApplicationItem[]>("/applications", { token }),
    get: (token: string, id: string) => request<ApplicationItem>(`/applications/${id}`, { token }),
    workspace: (token: string, id: string) =>
      request<ApplicationWorkspace>(`/applications/${id}/workspace`, { token }),
    create: (token: string, data: { university_id?: string; title?: string; notes?: string | null; status?: string; deadline?: string }) =>
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

  planner: {
    plan: (token: string) => request<PlannerPlan>("/planner/plan", { token }),
    tasksToday: (token: string) => request<PlannerTask[]>("/planner/tasks/today", { token }),
  },

  ai: {
    chat: (token: string, message: string, sessionId?: string) =>
      request<ChatResponse>("/ai/chat", {
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

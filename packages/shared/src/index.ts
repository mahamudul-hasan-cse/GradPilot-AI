export type User = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  role: string;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type University = {
  id: string;
  name: string;
  country: string;
  city: string | null;
  website: string | null;
  ranking: number | null;
  description: string | null;
  logo_url: string | null;
  is_active: boolean;
  created_at: string;
};

export type Scholarship = {
  id: string;
  title: string;
  provider: string;
  country: string | null;
  amount: string | null;
  currency: string | null;
  description: string | null;
  eligibility: string | null;
  deadline: string | null;
  application_url: string | null;
  is_active: boolean;
  created_at: string;
};

export type ApplicationStatus =
  | "draft"
  | "in_progress"
  | "submitted"
  | "accepted"
  | "rejected"
  | "withdrawn";

export type Application = {
  id: string;
  user_id: string;
  program_id: string | null;
  university_id: string | null;
  scholarship_id: string | null;
  status: ApplicationStatus;
  notes: string | null;
  submitted_at: string | null;
  deadline: string | null;
  created_at: string;
  updated_at: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  skip: number;
  limit: number;
};

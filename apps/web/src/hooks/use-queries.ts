"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import type { ProfileAnalysisRequest, StudentProfile } from "@/lib/api";

function numberFromProfile(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function ieltsFromProfile(profile: StudentProfile | null | undefined): number | null {
  return numberFromProfile(profile?.test_scores?.ielts);
}

function buildProfileAnalysisRequest(profile: StudentProfile | null | undefined): ProfileAnalysisRequest | null {
  const gpa = numberFromProfile(profile?.gpa);
  const gpaScale = numberFromProfile(profile?.gpa_scale) ?? 4;
  const ielts = ieltsFromProfile(profile);
  const degreeLevel = profile?.target_degree || profile?.education_level;
  const major = profile?.field_of_study;
  if (gpa === null || ielts === null || !degreeLevel || !major) return null;

  return {
    cgpa: Math.min(4, Number(((gpa * 4) / gpaScale).toFixed(2))),
    ielts,
    degree_level: degreeLevel,
    major,
    country_preferences: profile?.target_countries ?? [],
    work_experience_years: profile?.work_experience_years ?? 0,
    use_cache: true,
  };
}

export function useProfile() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["profile", session?.user?.id],
    queryFn: () => api.profile.get(session!.accessToken),
    enabled: !!session?.accessToken,
  });
}

export function useProfileAnalysis() {
  const { data: session } = useSession();
  const profileQuery = useProfile();
  const request = buildProfileAnalysisRequest(profileQuery.data);
  return useQuery({
    queryKey: ["profile-analysis", session?.user?.id],
    queryFn: () => api.profile.analyze(session!.accessToken, request!),
    enabled: !!session?.accessToken && !!request,
    retry: false,
  });
}

export function useDigitalTwin() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["digital-twin", session?.user?.id],
    queryFn: () => api.student.digitalTwin(session!.accessToken),
    enabled: !!session?.accessToken,
  });
}

export function useUniversityMatches() {
  const { data: session } = useSession();
  const profileQuery = useProfile();
  const analysisRequest = buildProfileAnalysisRequest(profileQuery.data);
  const budget = numberFromProfile(profileQuery.data?.budget_max) ?? 50000;
  const country = profileQuery.data?.target_countries?.[0] ?? null;
  return useQuery({
    queryKey: ["university-matches", session?.user?.id],
    queryFn: () =>
      api.recommendations.universities(session!.accessToken, {
        ...analysisRequest!,
        budget,
        country_preference: country,
        limit_per_tier: 5,
      }),
    enabled: !!session?.accessToken && !!analysisRequest,
    retry: false,
  });
}

export function useScholarshipMatches() {
  const { data: session } = useSession();
  const profileQuery = useProfile();
  const request = buildProfileAnalysisRequest(profileQuery.data);
  const country = profileQuery.data?.target_countries?.[0] ?? null;
  return useQuery({
    queryKey: ["scholarship-matches", session?.user?.id],
    queryFn: () =>
      api.recommendations.scholarships(session!.accessToken, {
        ...request!,
        country_preference: country,
        nationality: profileQuery.data?.nationality ?? null,
        limit: 5,
      }),
    enabled: !!session?.accessToken && !!request,
    retry: false,
  });
}

export function useApplications() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["applications", session?.user?.id],
    queryFn: () => api.applications.list(session!.accessToken),
    enabled: !!session?.accessToken,
  });
}

export function useDocuments() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["documents", session?.user?.id],
    queryFn: () => api.documents.list(session!.accessToken),
    enabled: !!session?.accessToken,
  });
}

export function useTimeline() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["timeline", session?.user?.id],
    queryFn: () => api.student.timeline(session!.accessToken),
    enabled: !!session?.accessToken,
  });
}

export function usePlannerTasksToday() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["planner-tasks-today", session?.user?.id],
    queryFn: () => api.planner.tasksToday(session!.accessToken),
    enabled: !!session?.accessToken,
    retry: false,
  });
}

export function useUniversitiesInfinite(q?: string, country?: string) {
  return useInfiniteQuery({
    queryKey: ["universities", q, country],
    queryFn: ({ pageParam = 0 }) =>
      api.universities.list({ q, country, skip: pageParam, limit: 20 }),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      const next = lastPage.skip + lastPage.limit;
      return next < lastPage.total ? next : undefined;
    },
  });
}

export function useScholarshipsInfinite(q?: string) {
  return useInfiniteQuery({
    queryKey: ["scholarships", q],
    queryFn: ({ pageParam = 0 }) =>
      api.scholarships.list({ q, skip: pageParam, limit: 20 }),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      const next = lastPage.skip + lastPage.limit;
      return next < lastPage.total ? next : undefined;
    },
  });
}

export function useUploadDocument() {
  const { data: session } = useSession();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, documentType }: { file: File; documentType?: string }) =>
      api.documents.upload(session!.accessToken, file, documentType),
    onMutate: async () => {
      toast.loading("Uploading document...", { id: "upload-doc" });
    },
    onSuccess: () => {
      toast.success("Document uploaded", { id: "upload-doc" });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Upload failed", { id: "upload-doc" });
    },
  });
}

export function useUpdateProfile() {
  const { data: session } = useSession();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof api.profile.update>[1]) =>
      api.profile.update(session!.accessToken, data),
    onSuccess: () => {
      toast.success("Profile updated");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile-analysis"] });
      queryClient.invalidateQueries({ queryKey: ["university-matches"] });
      queryClient.invalidateQueries({ queryKey: ["scholarship-matches"] });
      queryClient.invalidateQueries({ queryKey: ["digital-twin"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

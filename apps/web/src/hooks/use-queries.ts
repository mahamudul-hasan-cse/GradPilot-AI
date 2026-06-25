"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { toast } from "sonner";

import { api } from "@/lib/api";

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
  return useQuery({
    queryKey: ["profile-analysis", session?.user?.id],
    queryFn: () => api.profile.analyze(session!.accessToken),
    enabled: !!session?.accessToken,
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
  return useQuery({
    queryKey: ["university-matches", session?.user?.id],
    queryFn: () => api.recommendations.universities(session!.accessToken, { limit: 5 }),
    enabled: !!session?.accessToken,
    retry: false,
  });
}

export function useScholarshipMatches() {
  const { data: session } = useSession();
  return useQuery({
    queryKey: ["scholarship-matches", session?.user?.id],
    queryFn: () => api.recommendations.scholarships(session!.accessToken, { limit: 5 }),
    enabled: !!session?.accessToken,
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
      queryClient.invalidateQueries({ queryKey: ["digital-twin"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

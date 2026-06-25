"use client";

import { useSession } from "next-auth/react";

import { api } from "@/lib/api";

export function useAccessToken() {
  const { data: session } = useSession();
  return session?.accessToken ?? null;
}

export function useAuthenticatedApi() {
  const token = useAccessToken();
  return { token, api, isAuthenticated: !!token };
}

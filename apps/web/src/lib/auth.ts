import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import type { JWT } from "next-auth/jwt";

import { api } from "@/lib/api";

const TOKEN_REFRESH_SKEW_MS = 60_000;

async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const refreshed = await api.auth.refresh(token.refreshToken);
    return {
      ...token,
      accessToken: refreshed.access_token,
      refreshToken: refreshed.refresh_token,
      accessTokenExpiresAt: Date.now() + refreshed.expires_in * 1000,
      error: undefined,
    };
  } catch {
    return {
      ...token,
      accessToken: "",
      refreshToken: "",
      accessTokenExpiresAt: 0,
      error: "RefreshAccessTokenError",
    };
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: process.env.AUTH_SECRET,
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const tokens = await api.auth.login(
            credentials.email as string,
            credentials.password as string,
          );
          const user = await api.auth.me(tokens.access_token);

          return {
            id: user.id,
            email: user.email,
            name: user.full_name,
            role: user.role,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            accessTokenExpiresAt: Date.now() + tokens.expires_in * 1000,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  session: { strategy: "jwt", maxAge: 60 * 60 * 24 * 7 },
  pages: {
    signIn: "/login",
    newUser: "/register",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.accessTokenExpiresAt = user.accessTokenExpiresAt;
        token.role = user.role;
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
      }
      if (token.accessTokenExpiresAt && Date.now() < token.accessTokenExpiresAt - TOKEN_REFRESH_SKEW_MS) {
        return token;
      }
      if (token.refreshToken) {
        return refreshAccessToken(token);
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.accessToken = token.accessToken as string;
        session.refreshToken = token.refreshToken as string;
      }
      session.error = token.error;
      return session;
    },
  },
  trustHost: true,
});

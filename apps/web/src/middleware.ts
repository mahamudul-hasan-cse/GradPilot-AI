import { auth } from "@/lib/auth";

const protectedRoutes = [
  "/dashboard",
  "/profile",
  "/universities",
  "/scholarships",
  "/advisor",
  "/planner",
  "/applications",
  "/documents",
  "/timeline",
  "/notifications",
  "/settings",
];

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isProtected = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  const sessionExpired = req.auth?.expires ? new Date(req.auth.expires).getTime() <= Date.now() : false;
  const sessionInvalid = req.auth?.error === "RefreshAccessTokenError";

  if (isProtected && (!req.auth || sessionExpired || sessionInvalid)) {
    const loginUrl = new URL("/login", req.nextUrl.origin);
    // Only pass callbackUrl for non-error redirects so a broken session does
    // not keep bouncing the user to the same protected route on re-login.
    if (!sessionInvalid && !sessionExpired) {
      loginUrl.searchParams.set("callbackUrl", pathname);
    }
    return Response.redirect(loginUrl);
  }

  // Only redirect away from auth pages if the session is valid (no error state).
  // If there is a RefreshAccessTokenError the session exists but is broken —
  // letting the user stay on /login breaks the redirect loop and lets them
  // re-authenticate cleanly.
  if ((pathname === "/login" || pathname === "/register") && req.auth && !req.auth.error) {
    return Response.redirect(new URL("/dashboard", req.nextUrl.origin));
  }
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};

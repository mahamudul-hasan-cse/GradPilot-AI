import { auth } from "@/lib/auth";

const protectedRoutes = [
  "/dashboard",
  "/profile",
  "/universities",
  "/scholarships",
  "/advisor",
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

  if (isProtected && !req.auth) {
    const loginUrl = new URL("/login", req.nextUrl.origin);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return Response.redirect(loginUrl);
  }

  if ((pathname === "/login" || pathname === "/register") && req.auth) {
    return Response.redirect(new URL("/dashboard", req.nextUrl.origin));
  }
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes frontend nécessitant une session
const PROTECTED_PAGES = ["/agent", "/chat"];
// Préfixes d'API frontend à protéger (s'il y en a un jour côté Next)
const PROTECTED_API_PREFIX = "/api/";

// Nom du cookie de session (doit matcher le cookie posé par le backend auth)
const SESSION_COOKIE = "access_token";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const needsPageAuth = PROTECTED_PAGES.some(
    (p) => pathname === p || pathname.startsWith(p + "/")
  );
  const needsApiAuth = pathname.startsWith(PROTECTED_API_PREFIX);

  if (!needsPageAuth && !needsApiAuth) {
    return NextResponse.next();
  }

  const token = req.cookies.get(SESSION_COOKIE)?.value;

  // API : répondre 401 (pas de redirect) si pas de token
  if (needsApiAuth) {
    if (!token) {
      return NextResponse.json(
        { detail: "Non authentifié" },
        { status: 401 }
      );
    }
    return NextResponse.next();
  }

  // Pages : rediriger vers /login si pas de token
  if (!token) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/agent/:path*", "/chat/:path*", "/api/:path*"],
};

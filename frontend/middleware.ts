import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Authentification facultative en local : l'agent est accessible directement
const PROTECTED_PAGES: string[] = [];

// Nom du cookie de session
const SESSION_COOKIE = "access_token";

export function middleware(req: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [],
};

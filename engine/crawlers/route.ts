import { NextResponse } from "next/server";
import { newCsrfToken } from "@/server/security/csrf";

/**
 * GET /api/csrf
 * - returns { csrfToken }
 * - sets cookie csrf_token (readable by client, for double-submit)
 */
export async function GET() {
  const token = newCsrfToken();
  const res = NextResponse.json({ csrfToken: token });

  res.cookies.set("csrf_token", token, {
    httpOnly: false,
    secure: true,
    sameSite: "none",
    path: "/",
  });

  return res;
}

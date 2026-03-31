import crypto from "crypto";

export function newCsrfToken() {
  return crypto.randomBytes(32).toString("hex");
}

export function timingSafeEqual(a: string, b: string) {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) return false;
  return crypto.timingSafeEqual(ba, bb);
}

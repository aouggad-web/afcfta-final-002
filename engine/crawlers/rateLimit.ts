import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export type RateLimitPolicy = { windowSec: number; max: number };

/**
 * Simple fixed-window counter.
 * Good enough for protecting crawl/search endpoints.
 */
export async function rateLimit(key: string, limit: RateLimitPolicy) {
  const now = Math.floor(Date.now() / 1000);
  const bucket = Math.floor(now / limit.windowSec);
  const redisKey = `rl:${key}:${bucket}`;

  const count = await redis.incr(redisKey);
  if (count === 1) await redis.expire(redisKey, limit.windowSec + 2);

  return {
    allowed: count <= limit.max,
    remaining: Math.max(0, limit.max - count),
    resetInSec: limit.windowSec,
    count,
  };
}

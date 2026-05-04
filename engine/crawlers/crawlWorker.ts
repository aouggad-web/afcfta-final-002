import { db } from "@/server/db";
import { crawlQueue } from "@/server/db/schema/crawlQueue";
import { eq } from "drizzle-orm";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const WORK_DIR = "./worker-logs";

/**
 * Claim exactly one queued job (row lock inside transaction)
 */
async function claimJob() {
  return db.transaction(async (tx) => {
    const rows = await tx
      .select()
      .from(crawlQueue)
      // @ts-ignore drizzle supports .where with eq
      .where(eq(crawlQueue.status, "queued"))
      .limit(1)
      // row lock
      // @ts-ignore drizzle supports for("update") for MySQL/TiDB
      .for("update");

    if (!rows.length) return null;
    const job = rows[0];

    await tx
      .update(crawlQueue)
      .set({ status: "running", lockedAt: new Date(), startedAt: new Date() })
      // @ts-ignore
      .where(eq(crawlQueue.id, job.id));

    return job;
  });
}

async function runJob(job: any) {
  const logDir = path.join(WORK_DIR, job.jobId);
  fs.mkdirSync(logDir, { recursive: true });

  const logPath = path.join(logDir, "crawl.log");
  await db.update(crawlQueue).set({ logPath }).where(eq(crawlQueue.id, job.id));

  const out = fs.createWriteStream(logPath);

  // Adjust this path to your python script location
  const args = [
    "server/python/dza_tariff_connector.py",
    "crawl",
    "--out", "./data",
    "--max-pages", String(job.params.maxPages ?? 5000),
    "--rate", String(job.params.rate ?? 0.8),
    "--start-url", String(job.params.startUrl ?? "https://www.douane.gov.dz/spip.php?page=tarif_douanier"),
  ];

  const proc = spawn("python", args, { env: process.env });

  await db.update(crawlQueue).set({ pid: proc.pid ?? null }).where(eq(crawlQueue.id, job.id));

  proc.stdout.pipe(out);
  proc.stderr.pipe(out);

  return new Promise<number>((resolve) => {
    proc.on("close", (code) => resolve(code ?? -1));
  });
}

async function main() {
  // failover: if worker restarts, mark running jobs as failed
  await db
    .update(crawlQueue)
    .set({ status: "failed", endedAt: new Date(), errorMessage: "Worker restart" })
    // @ts-ignore
    .where(eq(crawlQueue.status, "running"));

  console.log("[crawlWorker] started");

  while (true) {
    const job = await claimJob();
    if (!job) {
      await new Promise((r) => setTimeout(r, 5000));
      continue;
    }

    let exitCode = -1;
    try {
      exitCode = await runJob(job);
      await db
        .update(crawlQueue)
        .set({
          status: exitCode === 0 ? "done" : "failed",
          exitCode,
          endedAt: new Date(),
        })
        // @ts-ignore
        .where(eq(crawlQueue.id, job.id));
    } catch (e: any) {
      await db
        .update(crawlQueue)
        .set({
          status: "failed",
          exitCode: -1,
          endedAt: new Date(),
          errorMessage: String(e?.message ?? e),
        })
        // @ts-ignore
        .where(eq(crawlQueue.id, job.id));
    }
  }
}

main();

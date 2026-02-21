import { mysqlTable, bigint, varchar, datetime, mysqlEnum, json, int } from "drizzle-orm/mysql-core";

export const crawlQueue = mysqlTable("crawl_queue", {
  id: bigint("id", { mode: "number" }).primaryKey().autoincrement(),
  jobId: varchar("job_id", { length: 64 }).notNull(),
  status: mysqlEnum("status", ["queued", "running", "done", "failed", "stopped"]).notNull().default("queued"),
  params: json("params").notNull(),

  pid: int("pid"),
  lockedAt: datetime("locked_at"),
  startedAt: datetime("started_at"),
  endedAt: datetime("ended_at"),
  exitCode: int("exit_code"),
  logPath: varchar("log_path", { length: 255 }),
  errorMessage: varchar("error_message", { length: 2048 }),

  createdAt: datetime("created_at").defaultNow().notNull(),
  updatedAt: datetime("updated_at").defaultNow().notNull(),
});

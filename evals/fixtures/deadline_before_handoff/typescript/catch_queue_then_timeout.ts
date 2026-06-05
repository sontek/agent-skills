import pLimit from "p-limit";

const limit = pLimit(4); // shared, concurrency-limited pool

export async function runWithRetry(sql: string, budgetMs: number) {
  const start = Date.now();
  for (let i = 0; i < 3; i++) {
    const remaining = Math.max(1, budgetMs - (Date.now() - start));
    // limit() queues the task when 4 are already running; the per-call timeout
    // only starts once the task runs, so queue wait isn't charged to `remaining`
    // and the total can overrun budgetMs under load.
    const r = await limit(() => withTimeout(runSql(sql), remaining));
    if (r.rows.length) return r;
  }
  return EMPTY;
}

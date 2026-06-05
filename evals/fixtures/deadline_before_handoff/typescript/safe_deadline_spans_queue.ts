import pLimit from "p-limit";

const limit = pLimit(4);

export async function runWithRetry(sql: string, budgetMs: number) {
  const start = Date.now();
  for (let i = 0; i < 3; i++) {
    const remaining = Math.max(1, budgetMs - (Date.now() - start));
    // The timeout wraps the queued task itself, so it counts the queue wait.
    const r = await withTimeout(limit(() => runSql(sql)), remaining);
    if (r.rows.length) return r;
  }
  return EMPTY;
}

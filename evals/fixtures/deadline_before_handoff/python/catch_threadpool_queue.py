import asyncio
from time import perf_counter


async def run_with_retry(sql, budget_secs):
    start = perf_counter()
    for _ in range(3):
        # Remaining budget computed HERE, before the to_thread handoff.
        remaining = max(1, budget_secs - int(perf_counter() - start))
        # asyncio.to_thread uses the shared default executor: under load the call
        # sits queued before _run_sql starts, and the DB statement_timeout (set
        # to `remaining` inside the worker) only begins once it runs. Queue time
        # is never charged, so total wall-clock can exceed budget_secs.
        columns, rows = await asyncio.to_thread(_run_sql, sql, remaining)
        if columns:
            return columns, rows
    return [], []

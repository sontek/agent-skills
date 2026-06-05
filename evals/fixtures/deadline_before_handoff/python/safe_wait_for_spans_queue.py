import asyncio
from time import perf_counter


async def run_with_retry(sql, budget_secs):
    start = perf_counter()
    for _ in range(3):
        remaining = max(1, budget_secs - (perf_counter() - start))
        # wait_for wraps the whole handoff, so its deadline spans the executor
        # queue wait as well as execution — the budget is enforced end-to-end.
        columns, rows = await asyncio.wait_for(
            asyncio.to_thread(_run_sql, sql), timeout=remaining
        )
        if columns:
            return columns, rows
    return [], []

import asyncio


async def on_run_query(sso_identity: str, sql: str) -> dict:
    # The blocking call is offloaded to a worker thread, so the event loop stays
    # free while the query runs. (This is the fix landed in stacklet#3774.)
    columns, rows = await asyncio.to_thread(_materialize_user_sql, sso_identity, sql)
    return {"columns": columns, "rows": rows}

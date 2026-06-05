async def on_run_query(sso_identity: str, sql: str) -> dict:
    # _materialize_user_sql opens a blocking DB session and runs the (possibly
    # slow) user query synchronously. Called directly in an async handler, it
    # stalls the whole event loop until the query returns — every concurrent
    # request stalls with it.
    columns, rows = _materialize_user_sql(sso_identity, sql)
    return {"columns": columns, "rows": rows}

def on_run_query(sso_identity: str, sql: str) -> dict:
    # Validation-gate case: this handler is SYNC (a plain function / WSGI view),
    # so a blocking DB call is expected and correct — there is no event loop to
    # stall. Must NOT flag.
    columns, rows = _materialize_user_sql(sso_identity, sql)
    return {"columns": columns, "rows": rows}

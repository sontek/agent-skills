async def execute_with_retry(query, timeout_secs, attempts=3):
    """`timeout_secs` is the whole-call wall-clock budget the caller relies on, but
    each retry attempt is handed the FULL timeout, so a slow-but-retried query can run
    up to attempts * timeout_secs — several times the documented budget. The deadline
    is not conserved across attempts.
    """
    for _ in range(attempts):
        try:
            return await run_sql(query, timeout=timeout_secs)
        except TransientError:
            continue
    raise TimeoutError

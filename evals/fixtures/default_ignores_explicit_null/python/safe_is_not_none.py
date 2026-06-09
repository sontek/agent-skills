def load_retry_config(raw: dict) -> int:
    """Same nullable config field: an explicit None falls through to the fallback via
    the `is not None` check, so a present `retries: null` yields 3, not None.
    """
    retries = raw.get("retries")
    return retries if retries is not None else 3

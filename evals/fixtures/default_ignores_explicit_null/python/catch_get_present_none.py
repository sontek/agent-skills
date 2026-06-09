def load_retry_config(raw: dict) -> int:
    """`raw` is parsed from a user JSON/YAML config whose schema documents `retries`
    as nullable (it may be present and explicitly null). dict.get returns the
    fallback only when the key is ABSENT — a present `retries: null` parses to a
    present key with value None, so this returns None, not 3. The None then flows
    into range()/comparison downstream and breaks.
    """
    return raw.get("retries", 3)

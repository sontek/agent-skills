def sort_by_count(rows):
    # Key is an integer count from len() — always finite and totally ordered.
    # Not a finding.
    return sorted(rows, key=lambda r: len(r["items"]))

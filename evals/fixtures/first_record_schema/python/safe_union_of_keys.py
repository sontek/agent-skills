def to_table(records):
    # Column set is the union of keys across all records, so a field that only
    # appears in later records is preserved.
    columns = list({k for r in records for k in r})
    rows = [{c: r.get(c) for c in columns} for r in records]
    return columns, rows

def to_table(records):
    # Column set taken from the FIRST record only. A later record that carries a
    # key the first one omits (an optional/nullable field) loses that column in
    # every row of the resulting table.
    columns = [k for k in records[0].keys()]
    rows = [{c: r.get(c) for c in columns} for r in records]
    return columns, rows

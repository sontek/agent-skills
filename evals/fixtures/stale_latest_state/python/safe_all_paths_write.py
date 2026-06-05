_latest = None


def record_snapshot(columns, rows):
    global _latest
    _latest = {"columns": columns, "rows": rows}


def get_latest_snapshot():
    return _latest


def run_query(sql):
    columns, rows = execute(sql)
    # Every producing path writes the store, including the empty-result case,
    # so the reader always reflects the latest turn. No staleness.
    record_snapshot(columns, rows)
    return render_table(columns, rows)


def reformat_last(plan):
    snap = get_latest_snapshot()
    return apply(plan, snap["rows"])

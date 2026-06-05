_latest = None


def record_snapshot(columns, rows):
    global _latest
    _latest = {"columns": columns, "rows": rows}


def get_latest_snapshot():
    return _latest


def run_query(sql):
    columns, rows = execute(sql)
    # Writes the snapshot only when there are rows. An empty-result turn returns
    # without recording, so the reader below keeps serving the PRIOR turn's rows.
    if columns and rows:
        record_snapshot(columns, rows)
    return render_table(columns, rows)


def reformat_last(plan):
    snap = get_latest_snapshot()          # expects the latest turn's result
    return apply(plan, snap["rows"])       # stale: rows from an earlier query

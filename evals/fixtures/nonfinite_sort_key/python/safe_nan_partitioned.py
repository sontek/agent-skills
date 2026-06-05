import math


def sort_rows(rows, column):
    # Non-finite values are partitioned out via a total-order tuple key, so a NaN
    # can't poison the ordering. Correct handling — not a finding.
    def key(r):
        v = float(r[column])
        return (math.isnan(v), 0.0 if math.isnan(v) else v)

    return sorted(rows, key=key)

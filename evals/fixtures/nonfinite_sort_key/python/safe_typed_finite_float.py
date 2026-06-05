from dataclasses import dataclass


@dataclass
class Row:
    amount: float  # populated from a validated numeric column, never parsed text


def sort_rows(rows: list[Row]):
    # Sorting plain finite floats from a typed source — no string parse, no
    # NaN-capable arithmetic, not nullable. This is the common, correct case and
    # must NOT be flagged just because the key is a float.
    return sorted(rows, key=lambda r: r.amount)

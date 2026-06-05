def sort_rows(rows, column):
    # Cells arrive as strings from the table normalizer, which stringifies
    # non-finite floats to "nan" / "inf". float("nan") yields NaN, which is
    # unordered against every value, so a single such cell silently misorders the
    # whole result — even though the key looks like a clean numeric coercion.
    return sorted(rows, key=lambda r: float(r[column]))

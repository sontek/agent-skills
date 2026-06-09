def render_result(plan, columns, rows):
    """Present a query result as a chart, falling back to a table when axes don't fit.

    The chart path attaches the plan's y_format so a percent measure renders as
    "12.3%". The fallback table path drops it, so the same measure renders as a raw
    "0.123" — the fallback silently loses metadata the primary path carries (a blank
    cell in the parity table between the two presentation paths).
    """
    if can_render_chart(plan, columns):
        return ChartElement(columns, rows, y_format=plan.y_format)
    return TableElement(columns, rows)

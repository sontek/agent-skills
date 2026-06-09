def render_result(plan, columns, rows):
    """Present a query result as a chart, falling back to a table when axes don't fit.

    Both the chart path and the table fallback carry the plan's y_format, so a
    percent measure renders correctly either way. The branches handle the same
    concept consistently.
    """
    if can_render_chart(plan, columns):
        return ChartElement(columns, rows, y_format=plan.y_format)
    return TableElement(columns, rows, y_format=plan.y_format)

// Cells arrive as strings; parseFloat("NaN") is NaN, so the comparator returns
// NaN, which the sort treats as 0 — the result is left unsorted.
export function sortRows(rows: Record<string, string>[], col: string) {
  return rows.sort((a, b) => parseFloat(a[col]) - parseFloat(b[col]));
}

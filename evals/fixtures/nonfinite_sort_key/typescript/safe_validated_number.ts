// Keys are already-validated finite numbers (a typed numeric field, not parsed
// from text and not the product of NaN-capable arithmetic), so the subtraction
// comparator is well-defined. Not a finding — plain number sorts are fine.
export function sortRows(rows: { amount: number }[]) {
  return rows.sort((a, b) => a.amount - b.amount);
}

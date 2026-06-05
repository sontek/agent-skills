export function toTable(records: Record<string, unknown>[]) {
  // Columns are the union of keys across every record.
  const columns = [...new Set(records.flatMap((r) => Object.keys(r)))];
  const rows = records.map((r) => pick(r, columns));
  return { columns, rows };
}

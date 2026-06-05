export function toTable(records: Record<string, unknown>[]) {
  // Columns derived from the first record; records that add keys later lose them
  // in the projected rows.
  const columns = Object.keys(records[0]);
  const rows = records.map((r) => pick(r, columns));
  return { columns, rows };
}

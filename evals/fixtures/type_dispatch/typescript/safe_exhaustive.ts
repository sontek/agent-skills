type Cell = string | number | boolean | null;

export function normalizeCell(value: unknown): Cell {
  switch (typeof value) {
    case "string":
    case "number":
    case "boolean":
      return value;
    case "object":
      return value === null ? null : JSON.stringify(value);
    default:
      // Catch-all: bigint / symbol / undefined / function degrade to a string
      // instead of being passed through unchanged.
      return String(value);
  }
}

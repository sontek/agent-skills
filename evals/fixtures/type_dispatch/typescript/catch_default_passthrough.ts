type Cell = string | number | boolean | null;

// Coerces known runtime types; the `default` returns the value as-is, so a
// Date / bigint / Map flows through and violates the Cell contract that
// downstream code (a typed serializer) relies on.
export function normalizeCell(value: unknown): Cell {
  switch (typeof value) {
    case "string":
    case "number":
    case "boolean":
      return value;
    case "object":
      if (value === null) return null;
      return JSON.stringify(value);
    default:
      return value as Cell; // passthrough — bigint, symbol, undefined slip through
  }
}

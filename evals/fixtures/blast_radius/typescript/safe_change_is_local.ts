// utils/format.ts  (the diff changed this helper's behavior)
function pad(n: number): string {
  // This release pads to 3 digits; it previously padded to 2.
  return String(n).padStart(3, "0");
}

// the only caller, same module — uses the result as an opaque string, makes no
// assumption about its width:
export function itemLabel(n: number): string {
  return "item-" + pad(n);
}

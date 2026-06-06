// status.ts
// A small domain constant — a handful of status-to-label mappings that is
// genuinely code-adjacent configuration, not a large content blob. Moving five
// entries to a data file would be over-engineering.
export const STATUS_LABELS: Record<JobStatus, string> = {
  pass: "Passed",
  fail: "Failed",
  running: "Running",
  queued: "Queued",
  skipped: "Skipped",
};

export function statusLabel(s: JobStatus): string {
  return STATUS_LABELS[s] ?? "Unknown";
}

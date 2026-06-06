// format.ts
// formatDuration has a unit test, but it is also imported and called by
// JobRow.tsx (production component) to render every job's elapsed time.
export function formatDuration(ms: number): string {
  const s = Math.round(ms / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

// JobRow.tsx (production caller):
export function JobRow({ job }: { job: Job }) {
  return <td>{formatDuration(job.elapsedMs)}</td>;
}

// format.test.ts
test("formats sub-minute durations", () => {
  expect(formatDuration(4200)).toBe("4s");
});

// dataGridDemo.tsx
export function DataGridDemo() {
  const rows = [
    { commit: "a1b2", job: "build", status: "pass", durationS: 42, retries: 0 },
    { commit: "a1b2", job: "test:unit", status: "pass", durationS: 118, retries: 0 },
    { commit: "a1b2", job: "test:e2e", status: "fail", durationS: 305, retries: 2 },
    { commit: "c3d4", job: "build", status: "pass", durationS: 39, retries: 0 },
    { commit: "c3d4", job: "test:unit", status: "fail", durationS: 121, retries: 1 },
    { commit: "c3d4", job: "test:e2e", status: "pass", durationS: 298, retries: 0 },
    { commit: "e5f6", job: "build", status: "pass", durationS: 44, retries: 0 },
    { commit: "e5f6", job: "test:unit", status: "pass", durationS: 117, retries: 0 },
    { commit: "e5f6", job: "test:e2e", status: "fail", durationS: 312, retries: 3 },
    { commit: "0789", job: "build", status: "pass", durationS: 41, retries: 0 },
    { commit: "0789", job: "test:unit", status: "pass", durationS: 119, retries: 0 },
    { commit: "0789", job: "test:e2e", status: "pass", durationS: 301, retries: 0 },
    // ...several dozen more hand-written rows
  ];
  return <Grid rows={rows} />;
}

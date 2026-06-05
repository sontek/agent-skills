let lastResult: Result | null = null;

// Auto-run writes the lastResult cache; the manual Run path renders but never
// updates it. "Repeat that" then reads lastResult and replays the auto run's
// data, not what the manual run just showed — stale.
export function autoRun(sql: string): Element {
  const r = execute(sql);
  lastResult = r;
  return renderTable(r);
}

export function manualRun(sql: string): Element {
  const r = execute(sql);
  return renderTable(r); // skips updating lastResult
}

export function repeatThat(plan: Plan): Element {
  return applyPlan(plan, lastResult!); // stale after a manualRun
}

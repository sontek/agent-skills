// No shared latest-pointer. The reformat operates on the result it is handed
// directly (the one the user is acting on), so there is nothing to go stale.
export function run(sql: string): Result {
  return execute(sql);
}

export function reformat(plan: Plan, current: Result): Element {
  return applyPlan(plan, current);
}

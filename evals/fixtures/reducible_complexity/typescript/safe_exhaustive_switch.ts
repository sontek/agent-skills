// events.ts
function reduce(state: State, event: Event): State {
  switch (event.type) {
    case "job_started":
      return { ...state, running: state.running + 1 };
    case "job_finished":
      return { ...state, running: state.running - 1, done: state.done + 1 };
    case "job_failed":
      return { ...state, running: state.running - 1, failed: state.failed + 1 };
    case "retry_scheduled":
      return { ...state, retries: state.retries + 1 };
    case "run_cancelled":
      return { ...state, running: 0, cancelled: true };
    case "run_reset":
      return initialState();
    default:
      return assertNever(event);
  }
}

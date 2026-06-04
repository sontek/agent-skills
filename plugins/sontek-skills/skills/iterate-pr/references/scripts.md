# Bundled Scripts

Reference for the four bundled scripts in `iterate-pr/scripts/`. All scripts run from the repo root via `${CLAUDE_SKILL_ROOT}` and require `uv` + `gh`.

## `scripts/fetch_pr_checks.py`

Fetches CI check status and extracts failure snippets from logs.

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_checks.py [--pr NUMBER]
```

Returns JSON:
```json
{
  "pr": {"number": 123, "branch": "feat/foo"},
  "summary": {"total": 5, "passed": 3, "failed": 2, "pending": 0},
  "checks": [
    {"name": "tests", "status": "fail", "log_snippet": "...", "run_id": 123},
    {"name": "lint", "status": "pass"}
  ]
}
```

## `scripts/fetch_pr_feedback.py`

Fetches and categorizes PR review feedback using the LOGAF scale (high/medium/low/bot/resolved).

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_feedback.py [--pr NUMBER]
```

Returns JSON with feedback categorized as:
- `high` - Must address before merge (`h:`, blocker, changes requested)
- `medium` - Should address (`m:`, standard feedback)
- `low` - Optional (`l:`, nit, style, suggestion)
- `bot` - Informational automated comments (Codecov, Dependabot, etc.)
- `resolved` - Already resolved threads

Review bot feedback (from Warden, Cursor, Bugbot, CodeQL, etc.) appears in `high`/`medium`/`low` with `review_bot: true` — it is NOT placed in the `bot` bucket.

## `scripts/reply_to_thread.py`

Replies to PR review threads in a single batched GraphQL mutation.

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/reply_to_thread.py THREAD_ID "body" [THREAD_ID "body" ...]
```

## `scripts/monitor_pr_checks.py`

Monitors PR checks until they all reach a terminal state. Retries transient `gh` failures, treats `skipping` and `cancel` as terminal, and waits for checks to register after a fresh push instead of exiting early. Used by the optional MonitorTool path in step 7 of the workflow.

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/monitor_pr_checks.py [--pr NUMBER]
```

Prints one terminal marker followed by a tab-separated check summary:
- `ALL_CHECKS_PASSED`
- `CHECKS_DONE_WITH_FAILURES`

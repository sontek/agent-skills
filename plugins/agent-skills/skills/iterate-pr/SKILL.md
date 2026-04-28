---
name: iterate-pr
description: Iterate on a PR until CI passes. Use when you need to fix CI failures, address review feedback, or continuously push fixes until all checks are green. Automates the feedback-fix-push-wait cycle.
---

# Iterate on PR Until CI Passes

Continuously iterate on the current branch until all CI checks pass and review feedback is addressed.

**Requires**: GitHub CLI (`gh`) authenticated.

**Requires**: The `uv` CLI for python package management, install guide at https://docs.astral.sh/uv/getting-started/installation/

**Important**: All scripts must be run from the repository root directory (where `.git` is located), not from the skill directory. Use the full path to the script via `${CLAUDE_SKILL_ROOT}`.

## Bundled Scripts

Four scripts power this skill. Full docs in [references/scripts.md](references/scripts.md):

- `fetch_pr_checks.py` — CI check status + failure log snippets
- `fetch_pr_feedback.py` — categorized review feedback (LOGAF scale: high/medium/low/bot/resolved)
- `reply_to_thread.py` — batched GraphQL mutation to reply to PR review threads
- `monitor_pr_checks.py` — watches CI to terminal state (used by MonitorTool path in step 7)

## Workflow

### 1. Identify PR

```bash
gh pr view --json number,url,headRefName
```

Stop if no PR exists for the current branch.

### 2. Gather Review Feedback

Run `${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_feedback.py` to get categorized feedback already posted on the PR.

### 3. Handle Feedback by LOGAF Priority

**Auto-fix (no prompt):**
- `high` - must address (blockers, security, changes requested)
- `medium` - should address (standard feedback)

When fixing feedback:
- Understand the root cause, not just the surface symptom
- If the same logical error appears in multiple places, fix all of them — not just the one the reviewer flagged
- **Test-first for testable findings.** For bugs, security gaps, performance regressions, or behavior changes, write a regression test BEFORE the fix. Confirm it fails without the fix, apply the fix, confirm it passes. If the new test unexpectedly passes without the fix, the feedback may be wrong — reply to clarify rather than silently skipping. Non-testable findings (naming, style, dead code, behavior-preserving refactors) apply directly — existing tests guard regressions.

This includes review bot feedback (items with `review_bot: true`). Treat it the same as human feedback:
- Real issue found → fix it
- False positive → skip, but explain why
- Never silently ignore review bot feedback — always verify the finding

**Prompt user for selection:**
- `low` - present numbered list and ask which to address:

```
Found 3 low-priority suggestions:
1. [l] "Consider renaming this variable" - @reviewer in api.py:42
2. [nit] "Could use a list comprehension" - @reviewer in utils.py:18
3. [style] "Add a docstring" - @reviewer in models.py:55

Which would you like to address? (e.g., "1,3" or "all" or "none")
```

**Skip silently:**
- `resolved` threads
- `bot` comments (informational only — Codecov, Dependabot, etc.)

### 4. Check CI Status

Run `${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_checks.py` to get structured failure data.

**Wait if pending:** If review bot checks (warden, cursor, bugbot, seer, codeql) are still running, wait before proceeding—they post actionable feedback that must be evaluated. Informational bots (codecov) are not worth waiting for.

### 5. Fix CI Failures

**Investigation is mandatory before any fix.** Do not guess, assume, or infer the cause from the check name or a surface-level reading of the error. You must trace the failure to its root cause in the actual code.

For each failure:

1. **Read the full log, not just the snippet.** Use `gh run view <run-id> --log-failed` if the snippet is truncated or ambiguous. Identify the exact failing assertion, exception, or lint rule.
2. **Trace backwards from the failure to the cause.** Follow the stack trace or error message into the source code. Read the relevant functions, types, and call sites — not just the line flagged. Do not stop at the first plausible explanation.
3. **Verify your understanding before touching code.** You should be able to state: "This fails because X, which was introduced/affected by Y." If you cannot state that clearly, keep investigating.
4. **Do not assume the feedback is wrong.** If a check flags something that seems incorrect, investigate fully before concluding it's a false positive. Most apparent false positives turn out to be real issues on closer inspection.
5. **If the same logical error appears in multiple places, fix all of them.** A type error, import issue, or logic bug at one call site usually repeats — search nearby code and related files for the same pattern and fix every instance, not just the one the check flagged.
6. **Fix the root cause with minimal, targeted changes.** Do not paper over the symptom with a workaround.
7. **Test-first for behavioral fixes.** For CI failures in existing tests, the failing test is already your TDD signal — fix the code, then confirm the test passes. For fixes that change runtime behavior but aren't yet covered (a lint rule catching a real bug, a missing edge case, a fix that uncovers an untested branch), write the regression test BEFORE the fix: confirm it fails, apply the fix, confirm it passes. Add the case to the nearest existing test file; don't create a whole new file. Pure style / lint / type / formatting fixes don't need tests.

### 6. Verify Locally, Then Commit via the `commit` skill

Before committing, verify your fixes locally:
- If you fixed a test failure: re-run that specific test locally
- If you fixed a lint/type error: re-run the linter or type checker on affected files
- For any code fix: run existing tests covering the changed code

If local verification fails, fix before proceeding — do not push known-broken code.

**Hand off to the `commit` skill to create the commit.** Do not craft commit messages inline — invoke the `commit` skill so message conventions (type prefix, character limits, AI attribution rules) are applied consistently. Then push:

```bash
git push
```

### 7. Monitor CI and Address Feedback

Poll CI status and review feedback in a loop instead of blocking:

1. Run `uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_checks.py` to get current CI status
2. If all checks passed → proceed to exit conditions
3. If any checks failed (none pending) → return to step 5
4. If checks are still pending:
   a. Run `uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_feedback.py` for new review feedback
   b. Address any new high/medium feedback immediately (same as step 3)
   c. If changes were needed, commit via the `commit` skill and push (this restarts CI), then continue polling
   d. Sleep 30 seconds (don't increase on subsequent iterations), then repeat from sub-step 1
5. After all checks pass, do a final feedback check: `sleep 10`, then run `uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_feedback.py`. Address any new high/medium feedback — if changes are needed, return to step 6.

#### MonitorTool optimization (Claude Code only)

Inside Claude Code, the `sleep 30` poll in sub-step 4d can be replaced with a background `MonitorTool` watch on `monitor_pr_checks.py`. This avoids burning conversation context on idle iterations. Other agents continue using the polling loop above — this is purely opt-in for Claude Code.

Run the bundled monitor through `MonitorTool` with `persistent: false`:

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/monitor_pr_checks.py
```

Set `timeout_ms` to roughly match the repo's normal CI duration. The script stays quiet until terminal state, so the monitor fires once when checks finish.

When `MonitorTool` reports completion, re-run `uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_checks.py`:
- All checks passed → continue to sub-step 5 above (final feedback check).
- Any checks failed → return to step 5 (Fix CI Failures).

If you push new commits while monitoring, the previous monitor was watching the prior CI run — start a fresh monitor against the new run set.

**Tradeoff:** the monitor only watches CI status, not review feedback. New review-bot comments that land while the monitor is running won't be surfaced until checks complete. If your repo has slow CI (>10 min) and fast review bots, prefer the polling loop above.

### 8. Repeat

If step 7 required code changes (from new feedback after CI passed), return to step 2 for a fresh cycle. CI failures during monitoring are already handled within step 7's polling loop.

## Exit Conditions

**Success:** All checks pass, post-CI feedback re-check is clean (no new unaddressed high/medium feedback including review bot findings), user has decided on low-priority items.

**Ask for help:** Same failure after 2 attempts, feedback needs clarification, infrastructure issues.

**Stop:** No PR exists, branch needs rebase.

## When scripts fail

If `uv` isn't installed or a bundled script fails, fall back to raw `gh` CLI rather than aborting. See [references/fallbacks.md](references/fallbacks.md) for the equivalent `gh` invocations and runtime/parsing-error handling.

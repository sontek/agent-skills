---
name: fix-issue
description: Implement a fix for a bug, issue, or failing behavior from scratch, reproduce-first. Use when asked to "fix this bug", "fix this issue", "resolve #123", "this is broken — make it work", "implement a fix for", or when handed an error/stack trace and expected to make a code change. Reproduce → fix → verify → edge cases → hand off. Distinct from `iterate-pr` (fixes CI/feedback on an existing PR), `optimize-perf` (perf only, benchmark-gated), `auto-review-code` (applies findings from a review), and `plan-implementation` (plans NEW multi-phase features without writing code). For a large multi-phase feature, run `plan-implementation` first, then this per phase.
---

# Fix Issue

Own the primary implement loop: a bug or issue comes in, you reproduce it, fix the root cause, prove the fix, and hand off a clean change. The discipline that makes this reliable is **reproduce before you fix** — a failing test or script written *first* is what separates a real fix from a plausible-looking edit.

This skill owns only the reproduce-fix-verify loop. It **delegates** finding-quality review to `review-code`, simplification to `simplify-code`, commits to `commit`, and PR creation to `create-pr`. Don't re-implement those here.

## When to use

- "Fix this bug", "resolve issue #123", "this endpoint 500s — fix it"
- A stack trace, failing test, or repro steps handed over with intent to change code
- A single, scoped defect or small feature where the change fits in a few files

## When NOT to use

- **NEW multi-phase feature** — run `plan-implementation` first; then use this skill per phase.
- **Existing PR with CI failures / review feedback** — use `iterate-pr`.
- **Performance regression measured in wall-clock** — use `optimize-perf` (benchmark-gated).
- **Applying findings a review already produced** — use `auto-review-code`.
- **Greenfield UI work** — use `frontend-design`.
- **You only need a diagnosis, not a change** — investigate directly; don't invoke this.

## Scope check (first, before any edit)

1. Restate the issue in one sentence: the observed wrong behavior and the expected behavior. If you can't, ask — don't guess at intent.
2. If the issue references a remote repo you don't have locally, use `librarian` to fetch it.
3. **Route by scope.** The deciding question: *can you name the root cause and the files it lives in before starting?*

   | Situation | Route |
   |---|---|
   | An `IMPLEMENTATION_PLAN_*.md` or plan-mode draft already exists for this work | **Working from a plan** (below) — execute it |
   | Root cause + files are clear; change fits a few files | **Fix directly** — go to The loop. The reproduce-first step *is* the plan. |
   | Root cause unknown, cross-cutting, multi-file, or spans multiple commits/PRs | **Plan first** — stop and run `plan-implementation`, then return here to execute it |

   When unsure between "fix directly" and "plan first," prefer a quick investigation (read the suspect files) before deciding — don't write a plan to discover the root cause, and don't start editing blind.

## Working from a plan

When a plan exists (an `IMPLEMENTATION_PLAN_*.md` at the repo root, or an in-conversation plan-mode draft), treat it as the source of truth and execute it phase by phase:

1. Read the plan. The **Phases** (with their quality gates) and the **Ideal State Criteria** (binary checkboxes, including anti-criteria) drive the work.
2. **Run The loop once per phase**, not once for the whole task:
   - The phase's **quality gate** becomes the verify step (step 4) for that phase.
   - Reproduce-first still applies *within* each phase — write the failing check for that phase's behavior before editing.
3. After each phase, tick the **Ideal State Criteria** it satisfies. The job is done when every criterion is checked (and no anti-criterion is violated) — that is the exit condition, replacing the single-issue "done" below.
4. If a phase reveals the plan is wrong (missing a phase, wrong ordering, a quality gate that can't be met), stop and update the plan via `plan-implementation` rather than improvising around it.

## The loop

### 1. Reproduce — write the failing check first

Before touching source, capture the bug as something that fails:

- **Prefer a test** in the repo's existing suite (`pytest`, `go test`, `vitest`, etc.) that asserts the *correct* behavior. Run it; confirm it **fails for the stated reason** (not an import error or wrong fixture).
- If a test is genuinely impractical (needs a running service, real upstream), write a minimal repro **script** under `/tmp` that prints the wrong result, and run it.
- If the failing check unexpectedly **passes**, the issue as reported is wrong or already fixed. Stop and report that with evidence rather than inventing a change.

This step is non-negotiable — it is the difference between this skill and an untested edit. Borrowed from `iterate-pr`'s test-first rule.

### 2. Find the root cause — not the symptom

Trace the failure to the actual cause in the code. Read the enclosing function, its callers, and the relevant config or tests. Do not patch the surface (swallow the exception, special-case the one input) when the cause is upstream.

- If the same logical defect exists in **multiple places**, fix all of them, not just the one in the report.
- Name the exact transformation before you make it. "Consider refactoring" is not a fix.
- **Escape hatch:** if the root cause turns out to be cross-cutting — it spans many files, needs a schema/API change, or is really several fixes wearing a trench coat — stop. This is now plan-shaped. Summarize what you found and run `plan-implementation`, then return via **Working from a plan**. Don't let a "quick fix" sprawl into an unplanned multi-file change.

### 3. Apply the minimal fix

Make the smallest change that addresses the root cause. Match the surrounding code's style, naming, and idioms. Don't fold in unrelated cleanups — those belong to a separate change (`simplify-code`, `auto-review-code`).

### 4. Verify — re-run the failing check

Run the test/script from step 1. It must now **pass**. If it doesn't, return to step 2; do not adjust the test to make it pass.

### 5. Edge cases and regression net

- Add assertions for the obvious adjacent cases: empty/null input, boundary values, the error path, the falsy-zero case. A bug usually has siblings.
- Run the existing test suite for the changed files (`pytest path/`, `go test ./...`). If anything regresses, fix it or revert — never ship a red suite.

### 6. Hand off

- Self-review the diff via `review-code` (branch mode). Address P0–P2 findings before proceeding.
- For the commit, use `commit`. For a PR, use `create-pr`. Don't craft either by hand.

## Conventions borrowed from mini-swe-agent

These keep the loop cheap and reliable:

- **Output hygiene.** When a command (test run, build, log fetch) produces more than ~10 KB of output, don't paste it whole — show head + tail, or `grep`/redirect-to-file and search. Pasting full output burns context for no gain.
- **Footgun removal.** When running tools that page or render progress bars, neutralize them up front: `PAGER=cat`, `GIT_PAGER=cat`, `TQDM_DISABLE=1`, `PIP_PROGRESS_BAR=off`. On macOS, `sed -i` needs an argument: `sed -i ''`.
- **Reproduce-first is the whole point.** mini-swe-agent's measured workflow is reproduce → fix → re-run → edge cases → submit. The reproduction step is what makes the rest trustworthy.

## Exit conditions

- **Done (direct fix)** — failing check now passes, edge cases covered, existing suite green, diff self-reviewed. Report and hand off.
- **Done (from a plan)** — every Ideal State Criterion checked, no anti-criterion violated, each phase's quality gate met. Report and hand off.
- **Cannot reproduce** — the failing check passes before any fix. Report with evidence; do not change code.
- **Escalated to planning** — the fix turned out cross-cutting/multi-phase (see escape hatch). Stop, summarize findings, run `plan-implementation`, then resume via **Working from a plan**.
- **Blocked** — root cause is in a dependency you can't change, or needs a product decision. Surface the specific blocker and ask.

## Final summary (emit to user)

```markdown
## Fix complete: <one-line issue restatement>

**Root cause:** <where and why — file:line>
**Fix:** <the transformation, file:line>
**Reproduction:** <test or script that failed before, passes now>
**Edge cases added:** <list, or "none needed">
**Test suite:** <passing / what ran>

Next: review the diff, then `commit` / `create-pr`.
```

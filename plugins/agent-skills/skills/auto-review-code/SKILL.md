---
name: auto-review-code
description: Automatically iterate review-code and simplify until no more safe fixes remain. Use when user wants to "auto-review-code", "auto-fix", run review-and-simplify on repeat, or clean up code without staying in the loop for each finding. Auto-applies local, low-risk fixes; batches risky changes for a single end-of-run approval pass.
---

# Auto Review Code

Loop: `review-code` → auto-apply safe fixes → `simplify` → auto-apply safe fixes, repeat until convergence or escalation. Collects risky changes into a single end-of-run approval bucket so the user isn't prompted per-finding.

## When to use

- User says "auto-review-code", "auto-fix", "clean up until it's clean", or similar
- User wants to stop manually alternating `review-code` and `simplify`
- Cleaning a feature branch before opening a PR

## When NOT to use

- Single-shot review only — use `review-code` directly
- CI-driven feedback loops — use `iterate-pr`
- Reviewing a plan or design — use `review-plan`

## Modes

Same as `review-code`. Pick one before starting; default `branch`.

- **`branch` (default)** — Scope is branch changes vs. main.
- **`paths`** — Scope is an explicit list of files or directories reviewed as-is. Requires the invoker to provide the list; do not default to whole-repo.

Pass the selected mode through to both `review-code` and `simplify` each round so scopes stay aligned.

## Auto-apply policy

A finding is **auto-applied without prompting** when ALL of these hold:

1. Priority is P1, P2, or P3 (P0 escalates — see below).
2. Fix is local: touches ≤5 files AND ≤~50 LOC of changes.
3. Fix does NOT introduce new modules, files, packages, or dependencies.
4. Fix does NOT change a public API signature, exported type, or config schema.
5. Fix is concrete. Counts as concrete if any of:
   - has a ` ```suggestion ` block,
   - specifies the exact code/text to insert, delete, or replace,
   - names a specific function/file/identifier with a single unambiguous transformation (e.g., "drop the conditional", "add `.filter(started_at__gte=start_dt)` before `.values(...)`").

   Hedge prose like "Optional —", "Defer until…", "Consider…", or "Acceptable as-is, but…" does NOT by itself disqualify a fix — only ambiguity about *what to do* disqualifies it. "Consider refactoring X to Y" with no specific transformation is NOT concrete.
6. Fix is not a *judgment-call* behavior change. The following count as auto-applicable behavior changes (small, additive, one-way improvements):
   - Additive observability: a new `logger.warn`/`logger.info`/`logger.debug` on an exceptional path; a `print` for CLI scripts.
   - A small UX flash (e.g., `messages.success/info/warning(request, "...")`) that surfaces previously-silent feedback. Does NOT include UI rewrites or copy changes that touch >1 user-visible string.
   - Differentiating previously-conflated error states (e.g., distinguishing "timeout" from "empty result" in a returned message) where no caller asserts on the old message.

   The following are NOT auto-applicable — flag for approval:
   - Changing the default value of a config flag, env var, or function kwarg.
   - Altering an error message asserted on in tests, parsed by callers, or part of a public API contract (grep tests for the message before applying).
   - Tightening validation on a path that currently accepts values matching the old contract — even if the values look "obviously invalid" — because callers may rely on the laxness.
   - Changing the return type or shape of a public function.

Otherwise: add to the **flagged-for-approval** bucket and continue the loop. Over-flagging is cheap; over-applying is expensive. When in doubt, flag.

## Hard-stop on P0

Any P0 finding stops the loop immediately. Do not auto-apply. Show the finding to the user and wait for direction. P0 means "drop everything, blocking" — it deserves a thinking pass, not a reflex fix.

## Test-first for testable fixes

Most correctness and behavior findings can be captured in a regression test. Prefer writing the test BEFORE applying the fix — this proves the finding is real, proves the fix addresses it, and locks in the repair against future regression. Without this step, we fix bugs that can silently come back.

**Testable (prefer TDD):**
- Correctness — null/undefined access, off-by-one, wrong operator, inverted conditions, missing await, race conditions
- Security — injection, broken access control, IDOR (scope an integration test to the vulnerable endpoint)
- Performance — N+1 queries (assert query count), unbounded loops (assert bounded behavior)
- Behavior changes — validation, error handling, edge cases

**Not cleanly testable (apply directly, no test needed):**
- Simplifications and behavior-preserving refactors — existing tests guard
- Dead code, unused imports, redundant wrappers
- Naming, comments, style, formatting
- Documentation-only changes

**TDD workflow for testable fixes:**

1. Locate the appropriate test file. Prefer adding a case to an existing test file over creating a new one. If no tests cover the area, create a new test file alongside the code following the repo's test layout.
2. Write a test that reproduces the finding and should currently fail.
3. Run the test. Confirm it fails for the expected reason.
   - If it unexpectedly passes, the finding may be wrong — skip the fix and move the finding to `flag-for-approval` with a note ("test written but passed unchanged — verify finding").
4. Apply the fix.
5. Run the new test. Confirm it passes. Also run the containing test file to catch regressions in nearby cases.
6. If either run fails, revert both the fix and the test, and flag the finding for approval.

**Standalone "add a regression test" findings.** Some findings have no underlying code fix — the fix *is* "add tests for this latent path" (e.g., "add three tests proving the worker releases the lock after each task"). Auto-apply IF:

- The tests are concrete: each case names specific inputs, the action under test, and the expected behavior. Vague asks like "add coverage for the dispatch path" are NOT concrete.
- ≤5 new test cases AND ≤100 LOC of test code total.
- Adds to an existing test file, OR creates a single new test file in an established test layout.
- Does not require new test fixtures, services, harness changes, or test infrastructure.

Workflow: write the tests, run them. They should pass against current code (these tests pin existing behavior, they don't reproduce a bug). If a test unexpectedly fails, the finding has uncovered a real bug — revert the test and escalate to the user with the failure output.

**When test infrastructure isn't available or slow:**
- No test framework detected (no `pytest`, `jest`, `go test`, `cargo test`, etc.): apply directly; log the finding with `testable: infra-missing` so the user sees the gap.
- Tests exist but are prohibitively slow (single test file takes >60s): apply directly; log `testable: infra-slow`. Do not skip TDD because it's inconvenient — only because it's actually blocked.
- Finding is in test code itself: apply directly (no meta-test needed).

Do NOT spend time standing up test infrastructure inside the loop. That's a separate decision for the user.

## Loop structure

For each round (cap at 5):

1. **Review phase.** Run the `review-code` skill in the configured mode. Capture all findings with fingerprints (see below).
2. **Triage findings.** For each finding, classify as: `p0-halt`, `auto-apply`, or `flag-for-approval`. If any `p0-halt`, escalate immediately and exit the loop.
3. **Check oscillation.** For each `auto-apply` candidate, check if the same fingerprint was already auto-applied in a previous round. If yes, move it to `flag-for-approval` with a note ("oscillation: applied in round N, re-flagged in round M") — do not apply again.
4. **Apply review fixes.** For each `auto-apply` fix, classify as testable or not (see "Test-first for testable fixes"). For testable fixes, write the failing test first, confirm it fails, apply the fix, confirm it passes. For non-testable fixes, apply directly. After each fix, run any cheap local verification available (type check, lint). If verification or the new test fails, revert both the fix and the test, and flag the finding.
5. **Simplify phase.** Run the `simplify` skill against the same scope. Triage its findings with the same policy and oscillation check. Simplify findings are usually non-testable refactors — apply directly, relying on existing tests as the regression guard. If a simplify finding changes behavior rather than preserving it, treat it as testable and TDD it.
6. **Log the round** to `.claude/auto-review-code-log.md` (see format below).
7. **Check exit conditions.**

## Exit conditions

Stop when any of these hit:

- **Convergence** — A full round (review phase + simplify phase) produced zero auto-applied fixes. This is the normal success exit.
- **Max rounds** — 5 rounds completed. Note the cap was hit in the summary; may indicate a deeper issue worth user review.
- **P0 hard-stop** — Exit to user for direction.
- **Oscillation** — A finding was auto-applied in an earlier round and has returned. Move to flagged bucket with oscillation note and continue; if the same fingerprint oscillates twice, exit the loop immediately with the log attached.
- **Verification failure loop** — If three consecutive fix attempts fail verification, stop and escalate. Something in the review or simplify output is producing broken fixes.

## Fingerprint format

Normalize each finding to a stable fingerprint so oscillation detection is reliable:

```
{relative_path}:{start_line}|{category}|{short_summary_slug}
```

- `category`: one of `correctness`, `performance`, `security`, `design`, `testing`, `quality`, `simplify`
- `short_summary_slug`: lowercase, hyphenated, ≤40 chars, derived from the finding title (e.g., `dead-import`, `missing-await`, `n-plus-one-query`)

Line numbers shift as fixes are applied — fingerprint matching for oscillation should allow ±3 lines of drift within the same file when the category and summary slug match.

## State log format

Write to `.claude/auto-review-code-log.md` at the repo root. Overwrite on each invocation (single-run file — users who want history can copy it). Ensure the parent `.claude/` directory exists; create it if needed.

```markdown
# Auto-review-code log

Mode: branch
Scope: main..HEAD (15 files)
Started: 2026-04-21T10:03:12Z

## Round 1 — review-code

- [P2] src/api/users.py:42 | quality | dead-import
  - action: auto-applied (non-testable: quality)
- [P1] src/api/users.py:118 | correctness | missing-await
  - action: auto-applied (test: tests/api/test_users.py::test_fetch_awaits_db_call — added, failed before, passes after)
- [P1] src/api/*.py | design | unify-error-handling-across-views
  - action: flagged (touches 12 files — exceeds local threshold)

## Round 1 — simplify

- src/api/users.py:60 | simplify | redundant-wrapper
  - action: auto-applied (non-testable: refactor — relying on existing tests)

## Round 2 — review-code

- (no findings)

## Round 2 — simplify

- (no findings)

## Exit: convergence (round 2)
```

## Final summary (emit to user)

After the loop exits, output a single summary. This is the only user-facing output during the run — no per-finding narration.

```markdown
## Auto-review-code complete

**Mode:** branch | **Scope:** main..HEAD | **Rounds:** 2 (converged)

**Auto-applied (3):**
- [P2] src/api/users.py:42 — removed dead import
- [P1] src/api/users.py:118 — added missing await (+ regression test: `tests/api/test_users.py::test_fetch_awaits_db_call`)
- src/api/users.py:60 — flattened redundant wrapper (simplify)

**Regression tests added:** 1
**Testable fixes applied without tests (infra missing or slow):** 0

**Flagged for approval (1):**

1. **[P1] Unify error handling across views** — `src/api/*.py`
   Review finding: each view re-implements its own try/except with inconsistent error shapes; consolidate to a shared handler.
   Why flagged: touches 12 files, crosses module boundary.
   To apply: review each affected file, then say "apply #1" or address manually.

**Oscillations caught:** 0
**Verification failures:** 0

Log: `.claude/auto-review-code-log.md`

Next: review the flagged items above. Run the normal review-code skill on any that need deeper analysis.
```

## Invoking sub-skills

This skill orchestrates `review-code` and `simplify`. For each phase, invoke the corresponding skill and apply its output per the policy above. Do not re-implement their checklists — follow those skills' own rules for what to flag and how to phrase findings.

Pass the mode (`branch` or `paths`) and scope through to each sub-skill invocation so they operate on the same code the auto-review-code loop is working on.

## User override mid-run

If the user interrupts mid-round with a correction (e.g., "don't auto-apply anything in migrations/", "stop on P1 too"), honor it for the remainder of the run, note it in the log, and continue.

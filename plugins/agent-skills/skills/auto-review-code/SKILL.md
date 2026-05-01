---
name: auto-review-code
description: Automatically iterate review-code and code-simplifier until no more safe fixes remain. Use when user wants to "auto-review-code", "auto-fix", run review-and-simplify on repeat, or clean up code without staying in the loop for each finding. Auto-applies local, low-risk fixes; batches risky changes for a single end-of-run approval pass.
---

# Auto Review Code

Loop: `review-code` → auto-apply safe fixes → `review-security` → auto-apply safe fixes → `code-simplifier` agent → auto-apply safe fixes, repeat until convergence or escalation. Collects risky changes into a single end-of-run approval bucket so the user isn't prompted per-finding.

## When to use

- User says "auto-review-code", "auto-fix", "clean up until it's clean", or similar
- User wants to stop manually alternating `review-code`, `review-security`, and the `code-simplifier` agent
- Cleaning a feature branch before opening a PR

## When NOT to use

- Single-shot review only — use `review-code` directly
- CI-driven feedback loops — use `iterate-pr`
- Reviewing a plan or design — use `review-plan`

## Modes

Same as `review-code`. Pick one before starting; default `branch`.

- **`branch` (default)** — Scope is branch changes vs. main.
- **`paths`** — Scope is an explicit list of files or directories reviewed as-is. Requires the invoker to provide the list; do not default to whole-repo.

Pass the selected mode through to `review-code`, `review-security`, and the `code-simplifier` agent each round so scopes stay aligned.

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

When you flag a finding, capture the dossier *now* while the context is fresh — don't defer it to summary time. For each flagged item, record: a plain-language **What this would change**, concrete **Pros** and **Cons** of applying it (with at least one example each — actual file/line, actual scenario, actual cost), and a **Recommendation** with explicit confidence. The recommendation rule:

- **Only recommend `apply` or `skip` when you have a real basis** (you've read the surrounding code, you understand the trade-off, you'd defend the call). State confidence as `high` or `medium` and one short reason.
- **If you don't have a real basis, say `no strong opinion — depends on <the open question>`.** Naming the question is the work — it's what unblocks the user. Do not fabricate a recommendation to look decisive.

Hedge prose like "Consider…", "Worth thinking about…", or "May be acceptable as-is" is not a recommendation — convert it into one of the three forms above before flagging.

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

**Standalone "add a regression test" findings.** Some findings have no underlying code fix — the fix *is* "add tests for this latent path" (e.g., "add three tests proving the worker releases the lock after each task"). This is a sub-policy that overrides criterion 2's ≤~50 LOC cap (test code is bulkier than fix code); the other criteria still apply. Auto-apply IF:

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
2. **Triage findings.** For each finding, classify as: `p0-halt`, `auto-apply`, or `flag-for-approval`. If any `p0-halt`, escalate immediately and exit the loop. For each `flag-for-approval` finding, build the What / Pros / Cons / Recommendation dossier per the Auto-apply policy section before continuing — do not defer it to summary time.
3. **Check oscillation.** For each `auto-apply` candidate, check if the same fingerprint was already auto-applied in a previous round. If yes, move it to `flag-for-approval` with a note ("oscillation: applied in round N, re-flagged in round M") — do not apply again.
4. **Apply review fixes.** For each `auto-apply` fix, classify as testable or not (see "Test-first for testable fixes"). For testable fixes, write the failing test first, confirm it fails, apply the fix, confirm it passes. For non-testable fixes, apply directly. After each fix, run any cheap local verification available (type check, lint). If verification or the new test fails, revert both the fix and the test, and flag the finding.
5. **Security phase.** Run the `review-security` skill against the same scope. Map its severities to the auto-apply policy:
   - **Critical → P0 hard-stop.** RCE, SQL injection to data, auth bypass, hardcoded production secrets. Escalate to the user immediately and exit the loop.
   - **High → P1.** Eligible for auto-apply if criteria 2–6 hold; otherwise flag. Security-driven changes (parameterizing queries, escaping output, adding allow-list validation against an injection or SSRF vector) count as auto-applicable behavior changes — they remove exploitability rather than altering documented behavior.
   - **Medium → flag for approval.** Often surfaces as `Needs Verification` from `review-security` — these are open questions, not concrete fixes. Add to the flagged bucket with the verification question intact.
   - **Low** is not reported by `review-security`.

   Apply the same triage (step 2), oscillation (step 3), and TDD-where-testable (step 4) rules. Most security findings are testable: write a failing test that demonstrates the exploit (for injection/IDOR/SSRF: exercise the vulnerable path with attacker-controlled input and assert it's rejected), apply the fix, confirm the test passes.
6. **Simplify phase.** Invoke the `code-simplifier` agent via the Task tool (`subagent_type: code-simplifier`) against the same scope. The agent returns a per-file change report; treat each entry as a finding, triage with the same policy and oscillation check. Simplifier findings are usually non-testable refactors — apply directly, relying on existing tests as the regression guard. If a simplifier finding changes behavior rather than preserving it, treat it as testable and TDD it.
7. **Log the round** to `.claude/auto-review-code-log.md` (see format below).
8. **Check exit conditions.**

## Exit conditions

Stop when any of these hit:

- **Convergence** — A full round (review phase + security phase + simplify phase) produced zero auto-applied fixes. This is the normal success exit.
- **Max rounds** — 5 rounds completed. Note the cap was hit in the summary; may indicate a deeper issue worth user review.
- **P0 hard-stop** — Exit to user for direction. Triggered by either a `review-code` P0 finding or a `review-security` Critical finding.
- **Oscillation** — A finding was auto-applied in an earlier round and has returned. Move to flagged bucket with oscillation note and continue; if the same fingerprint oscillates twice, exit the loop immediately with the log attached.
- **Verification failure loop** — If three consecutive fix attempts fail verification, stop and escalate. Something in the review, security, or simplifier output is producing broken fixes.

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

## Round 1 — review-security

- [High] src/api/search.py:88 | security | sql-injection-search-query
  - action: auto-applied (test: tests/api/test_search.py::test_rejects_quote_injection — added, failed before, passes after)
- [Medium] src/api/upload.py:24 | security | path-traversal-needs-verification
  - action: flagged (Needs Verification: confirm filename is sanitized upstream by the multipart parser)

## Round 1 — code-simplifier

- src/api/users.py:60 | simplify | redundant-wrapper
  - action: auto-applied (non-testable: refactor — relying on existing tests)

## Round 2 — review-code

- (no findings)

## Round 2 — review-security

- (no findings)

## Round 2 — code-simplifier

- (no findings)

## Exit: convergence (round 2)
```

## Final summary (emit to user)

After the loop exits, output a single summary. This is the only user-facing output during the run — no per-finding narration.

````markdown
## Auto-review-code complete

**Mode:** branch | **Scope:** main..HEAD | **Rounds:** 2 (converged)

**Auto-applied (4):**
- [P2] src/api/users.py:42 — removed dead import
- [P1] src/api/users.py:118 — added missing await (+ regression test: `tests/api/test_users.py::test_fetch_awaits_db_call`)
- [Sec-High] src/api/search.py:88 — parameterized search query (+ regression test: `tests/api/test_search.py::test_rejects_quote_injection`)
- src/api/users.py:60 — flattened redundant wrapper (code-simplifier)

**Regression tests added:** 2
**Testable fixes applied without tests (infra missing or slow):** 0

**Flagged for approval (2):**

Each flagged item uses this format. Don't omit fields — if pros/cons/recommendation aren't filled in, the user has to ask for them anyway.

```
N. **[Priority] Title** — `location`
   **What this would change:** 1–2 sentences in plain language. Name the before/after behavior, not just the abstract concept.
   **Pros (apply it):** concrete benefit(s), with at least one example. e.g., "removes one DB round-trip per request — `views.search` currently runs N+1 over `result.items`."
   **Cons (apply it):** concrete cost(s) or risk(s), with at least one example. e.g., "12 files touched; conflicts with the in-flight users-API refactor on branch `feat/users-v2`."
   **Recommendation:** `apply` (confidence: high|medium) — one-line reason. OR `skip` (confidence: …) — one-line reason. OR `no strong opinion` — depends on <the open question>. Pick exactly one. Don't recommend without a basis.
   **To apply:** specific next action (e.g., `say "apply #N"`, or `decide on <question>, then re-run /auto-review-code`).
```

1. **[P1] Unify error handling across views** — `src/api/*.py`
   **What this would change:** Replace per-view try/except blocks with a single decorator (`@handle_api_errors`) on each view, returning a uniform `{error, code, request_id}` shape. Today, `users.py` returns `{detail: …}`, `search.py` returns `{message: …}`, and `upload.py` re-raises.
   **Pros (apply it):** Frontend can drop three error-shape branches in `client/src/api.ts:142`. New views inherit correct logging without each author remembering. Removes ~80 lines of duplicated try/except across the 12 views.
   **Cons (apply it):** Touches 12 files; conflicts with `feat/users-v2` which is rewriting `users.py` error paths this week. Frontend has to update its error-shape matcher in the same release or it'll log spurious "unknown error shape" warnings.
   **Recommendation:** `no strong opinion` — depends on whether `feat/users-v2` lands first. If yes, this is straightforward; if no, sequencing pain outweighs the cleanup.
   **To apply:** Confirm the merge order with the users-v2 author, then say "apply #1".

2. **[Sec-Med] Path traversal needs verification** — `src/api/upload.py:24`
   **What this would change:** Add `os.path.basename(filename)` before joining with the upload directory, plus a regression test asserting `../../etc/passwd` is rejected. Today the filename from the multipart parser is interpolated directly into the destination path.
   **Pros (apply it):** Closes a path-traversal vector if the upstream parser doesn't already strip separators. Cheap defense-in-depth (one line + one test). Test pins the behavior so future parser swaps can't silently regress it.
   **Cons (apply it):** If the parser already sanitizes, the change is dead code — minor noise. The test could mask a real upstream regression by passing on the local sanitizer instead of the parser.
   **Recommendation:** `apply` (confidence: medium) — defense-in-depth is cheap and the regression test catches a future parser swap.
   **To apply:** Say "apply #2", or trace `request.files` to the multipart parser first if you'd rather verify the parser sanitizes before adding a redundant guard.

**Oscillations caught:** 0
**Verification failures:** 0

Log: `.claude/auto-review-code-log.md`

Next: review the flagged items above. Run the normal `review-code` or `review-security` skills on any that need deeper analysis.
````

## Invoking sub-skills and sub-agents

This skill orchestrates three sub-capabilities per round, in order:

1. **`review-code`** — invoke as a sub-skill in the configured mode (`branch` or `paths`).
2. **`review-security`** — invoke as a sub-skill in the same mode. It accepts the same `branch` / `paths` scope; pass it through.
3. **`code-simplifier`** — invoke via the Task tool with `subagent_type: "code-simplifier"`. This is an agent, not a skill: it runs in isolated context and returns a per-file change report. Pass the same scope so it focuses on the right files.

For each phase, apply the sub-skill or sub-agent's output per the auto-apply policy above. Do not re-implement their checklists — follow each one's own rules for what to flag and how to phrase findings.

Pass the mode and scope through to each invocation so they operate on the same code the auto-review-code loop is working on.

## User override mid-run

If the user interrupts mid-round with a correction (e.g., "don't auto-apply anything in migrations/", "stop on P1 too"), honor it for the remainder of the run, note it in the log, and continue.

---
name: auto-review
description: Automatically iterate review-code and simplify until no more safe fixes remain. Use when user wants to "auto-review", "auto-fix", run review-and-simplify on repeat, or clean up code without staying in the loop for each finding. Auto-applies local, low-risk fixes; batches risky changes for a single end-of-run approval pass.
---

# Auto Review

Loop: `review-code` → auto-apply safe fixes → `simplify` → auto-apply safe fixes, repeat until convergence or escalation. Collects risky changes into a single end-of-run approval bucket so the user isn't prompted per-finding.

## When to use

- User says "auto-review", "auto-fix", "clean up until it's clean", or similar
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
5. Fix is concrete — either a ` ```suggestion ` block or an unambiguous description of the replacement. "Consider refactoring X to Y" without concrete code is NOT concrete.
6. Fix is not itself a behavior change whose correctness depends on business-logic judgment (e.g., changing a default, altering an error message used by callers, tightening validation that could reject existing inputs).

Otherwise: add to the **flagged-for-approval** bucket and continue the loop. Over-flagging is cheap; over-applying is expensive. When in doubt, flag.

## Hard-stop on P0

Any P0 finding stops the loop immediately. Do not auto-apply. Show the finding to the user and wait for direction. P0 means "drop everything, blocking" — it deserves a thinking pass, not a reflex fix.

## Loop structure

For each round (cap at 5):

1. **Review phase.** Run the `review-code` skill in the configured mode. Capture all findings with fingerprints (see below).
2. **Triage findings.** For each finding, classify as: `p0-halt`, `auto-apply`, or `flag-for-approval`. If any `p0-halt`, escalate immediately and exit the loop.
3. **Check oscillation.** For each `auto-apply` candidate, check if the same fingerprint was already auto-applied in a previous round. If yes, move it to `flag-for-approval` with a note ("oscillation: applied in round N, re-flagged in round M") — do not apply again.
4. **Apply review fixes.** Apply each `auto-apply` fix one at a time. After each fix, run any cheap local verification available (type check, lint, or tests if fast) before the next fix. If verification fails, revert that fix and flag it.
5. **Simplify phase.** Run the `simplify` skill against the same scope. Triage its findings with the same policy and oscillation check. Apply auto-apply fixes one at a time with the same verification.
6. **Log the round** to `.claude/auto-review-log.md` (see format below).
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

Write to `.claude/auto-review-log.md` at the repo root. Overwrite on each invocation (single-run file — users who want history can copy it). Ensure the parent `.claude/` directory exists; create it if needed.

```markdown
# Auto-review log

Mode: branch
Scope: main..HEAD (15 files)
Started: 2026-04-21T10:03:12Z

## Round 1 — review-code

- [P2] src/api/users.py:42 | quality | dead-import
  - action: auto-applied
- [P1] src/api/users.py:118 | correctness | missing-await
  - action: auto-applied
- [P1] src/api/*.py | design | unify-error-handling-across-views
  - action: flagged (touches 12 files — exceeds local threshold)

## Round 1 — simplify

- src/api/users.py:60 | simplify | redundant-wrapper
  - action: auto-applied

## Round 2 — review-code

- (no findings)

## Round 2 — simplify

- (no findings)

## Exit: convergence (round 2)
```

## Final summary (emit to user)

After the loop exits, output a single summary. This is the only user-facing output during the run — no per-finding narration.

```markdown
## Auto-review complete

**Mode:** branch | **Scope:** main..HEAD | **Rounds:** 2 (converged)

**Auto-applied (3):**
- [P2] src/api/users.py:42 — removed dead import
- [P1] src/api/users.py:118 — added missing await
- src/api/users.py:60 — flattened redundant wrapper (simplify)

**Flagged for approval (1):**

1. **[P1] Unify error handling across views** — `src/api/*.py`
   Review finding: each view re-implements its own try/except with inconsistent error shapes; consolidate to a shared handler.
   Why flagged: touches 12 files, crosses module boundary.
   To apply: review each affected file, then say "apply #1" or address manually.

**Oscillations caught:** 0
**Verification failures:** 0

Log: `.claude/auto-review-log.md`

Next: review the flagged items above. Run the normal review-code skill on any that need deeper analysis.
```

## Invoking sub-skills

This skill orchestrates `review-code` and `simplify`. For each phase, invoke the corresponding skill and apply its output per the policy above. Do not re-implement their checklists — follow those skills' own rules for what to flag and how to phrase findings.

Pass the mode (`branch` or `paths`) and scope through to each sub-skill invocation so they operate on the same code the auto-review loop is working on.

## User override mid-run

If the user interrupts mid-round with a correction (e.g., "don't auto-apply anything in migrations/", "stop on P1 too"), honor it for the remainder of the run, note it in the log, and continue.

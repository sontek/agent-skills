---
name: auto-review-plan
description: Automatically iterate review-plan against a plan until no safe blocking edits remain. Use when user wants to "auto-review-plan", "auto-fix the plan", tighten a plan without staying in the loop for each finding, or harden an `IMPLEMENTATION_PLAN_*.md` / `REFACTOR_PLAN_*.md` / plan-mode draft before implementation. Auto-applies small, concrete blocking edits; batches structural recommendations for a single end-of-run approval pass.
---

# Auto Review Plan

Loop: `review-plan` → auto-apply safe plan edits, repeat until convergence or escalation. Collects structural recommendations into a single end-of-run approval bucket so the user isn't prompted per-finding.

This skill is the plan-side analog of `auto-review`. It tightens a plan *before* implementation starts, rather than cleaning code after.

## When to use

- User says "auto-review-plan", "auto-fix the plan", "tighten the plan", or similar
- User wants to stop manually re-running `review-plan` after each round of edits
- Hardening an `IMPLEMENTATION_PLAN_*.md`, `REFACTOR_PLAN_*.md`, or an in-conversation plan-mode draft before starting work

## When NOT to use

- Single-shot plan critique only — use `review-plan` directly
- Reviewing code rather than a plan — use `auto-review` or `review-code`
- Creating a plan from scratch — use `plan-implementation` or `plan-refactor`

## Target plan

The skill supports two targets — pick whichever matches the source. The loop is identical; only the "where the edits live" step differs.

### File-based plan (preferred)

Order of preference:

1. **User-supplied path.** If the user pointed at a specific file, use it.
2. **Plan file at repo root.** `IMPLEMENTATION_PLAN_<feature>.md` or `REFACTOR_PLAN_<feature>.md`. If exactly one matches, use it. If multiple match and the user didn't name one, ask which.

Edits are applied with the `Edit` tool against the file, then the file is re-read for the next round.

### In-conversation plan (plan-mode draft or inline message)

If no plan file exists but the assistant recently drafted a plan via `ExitPlanMode` or inline in a message, use that text as the target.

There is no file to edit — hold the working plan text in conversation state. Each round:

1. Pass the current plan text to `review-plan` (inline, as the skill already supports).
2. Produce a new full plan text with the auto-apply edits merged in. This replaces the prior working version.
3. Feed that new text into the next round.

At exit, emit the final revised plan text as part of the user summary so the user can paste it back into plan mode (or accept it as the working plan). Do not persist the in-conversation plan to a file unless the user asks.

If neither a file nor a recent in-conversation plan exists, stop and tell the user to create one first (via `plan-implementation` or `plan-refactor`), or to paste/point at one. Do not invent a plan.
3. **No file found.** Stop and tell the user to create the plan first (via `plan-implementation` or `plan-refactor`), or to pass a path. Do not invent a plan file.

## Auto-apply policy

A finding is **auto-applied without prompting** when ALL of these hold:

1. Finding comes from the `Blocking concerns` or `Recommended plan edits` section of the `review-plan` output. `Worth considering` and `Long-term watch-outs` are advisory — add them to the flagged bucket rather than the plan.
2. Fix is concrete — either a specific replacement ("change the phase 2 rollout step from X to Y") or an anchored insertion ("add an error-state bullet under phase 3"). Vague asks like "think harder about scale" are NOT concrete.
3. Fix is localized — touches one section or phase of the plan AND ≤~40 lines of plan text.
4. Fix does NOT require new dependencies, services, packages, or external systems beyond what the plan already names.
5. Fix does NOT rewrite the problem statement, goal, success criteria, or scope boundary.
6. Fix does NOT delete, merge, split, or reorder existing phases. Adding a single new phase AT THE END (e.g., a cleanup phase) is fine; structural reshuffling is not.
7. Fix does NOT change the plan's verdict category itself (e.g., a finding that amounts to "reconsider whether this is the right approach" escalates — see below).

Otherwise: add to the **flagged-for-approval** bucket and continue the loop. Over-flagging is cheap; over-applying is expensive. When in doubt, flag. Plans are cheaper to re-review than to re-litigate, so err toward the user.

## Hard-stop on "Rethink approach"

If `review-plan` returns a verdict of `Rethink approach`, stop the loop immediately. Do not auto-apply anything from that round. Show the full review to the user and wait for direction. "Rethink" means the plan has a problem that tactical edits won't fix — it deserves a thinking pass, not a reflex edit.

## Loop structure

For each round (cap at 3):

1. **Review phase.** Invoke the `review-plan` skill against the target plan file. Capture all findings with fingerprints (see below) and the returned verdict.
2. **Check verdict.** If verdict is `Rethink approach`, hard-stop and exit to the user.
3. **Triage findings.** For each finding, classify as: `auto-apply` or `flag-for-approval` per the policy above.
4. **Check oscillation.** For each `auto-apply` candidate, check if the same fingerprint was already auto-applied in a previous round. If yes, move it to `flag-for-approval` with a note ("oscillation: applied in round N, re-flagged in round M") — do not apply again. If the same fingerprint oscillates twice, exit the loop immediately.
5. **Apply plan edits.**
   - *File-based:* edit the plan file in place. Use `Edit` with narrow `old_string` / `new_string` anchored to the finding's section so unrelated text isn't disturbed. After each edit, re-read the plan file to confirm the change landed.
   - *In-conversation:* produce a revised full plan text that merges the auto-apply edits into the prior working version. Keep the revised text in conversation state as the canonical plan for the next round. Do not re-emit it to the user between rounds.
6. **Log the round** to `.claude/auto-review-plan-log.md` (see format below).
7. **Check exit conditions.**

## Exit conditions

Stop when any of these hit:

- **Convergence** — A full round produced zero auto-applied edits (either no blocking findings, or all blocking findings were flagged). This is the normal success exit.
- **Max rounds** — 3 rounds completed. Note the cap was hit; may indicate the plan needs a human pass before iterating further.
- **Rethink verdict** — Hard-stop, exit to user.
- **Oscillation (twice)** — Same fingerprint flipped in and out across rounds. Exit with the log attached.
- **Edit failure loop** — If three consecutive edit attempts fail to land (file-based: `old_string` no longer matches after drift; in-conversation: revised text loses a section the next round's fingerprints refer to), stop and escalate with the current log.

## Fingerprint format

Normalize each finding to a stable fingerprint so oscillation detection is reliable across rounds:

```
{plan_id}:{section_or_phase}|{category}|{short_summary_slug}
```

- `plan_id`: the plan file path for file-based targets, or a stable tag like `plan-mode-draft` (or a short slug derived from the plan's title heading) for in-conversation targets.
- `section_or_phase`: the section header or phase label the finding targets (e.g., `Phase 2 — Rollout`, `Goals`, `Testing`). Use the literal heading text, lowercased and trimmed.
- `category`: one of `scope`, `architecture`, `phase-ordering`, `missing-gate`, `missing-state`, `clarity`, `dependency`, `testing`, `ux`
- `short_summary_slug`: lowercase, hyphenated, ≤40 chars, derived from the finding title (e.g., `missing-rollback-plan`, `unspecified-error-state`, `no-telemetry-gate`)

Section names are more stable than line numbers for plans, which get re-sectioned as edits apply. Fingerprint matching for oscillation should allow for minor section-title wording drift within the same plan when the category and summary slug match.

## State log format

Write to `.claude/auto-review-plan-log.md` at the repo root. Overwrite on each invocation (single-run file — users who want history can copy it). Ensure the parent `.claude/` directory exists; create it if needed.

```markdown
# Auto-review-plan log

Target: IMPLEMENTATION_PLAN_checkout-redesign.md  (or: plan-mode draft — "Checkout Redesign")
Started: 2026-04-24T10:03:12Z

## Round 1 — review-plan

Verdict: Revise before starting

- [Blocking] Phase 2 — Rollout | missing-gate | no-rollback-plan
  - action: auto-applied (added rollback step under Phase 2 — Rollout)
- [Blocking] Phase 3 — Migration | missing-state | unspecified-failure-mode
  - action: auto-applied (added failure-mode bullet under Phase 3 — Migration)
- [Blocking] Goals | scope | unclear-success-criteria
  - action: flagged (requires product-level decision on what "success" means)
- [Watch] Phase 4 — Cleanup | architecture | long-term-coupling
  - action: flagged (advisory — Worth considering)

## Round 2 — review-plan

Verdict: Ready to implement

- (no blocking findings)

## Exit: convergence (round 2)
```

## Final summary (emit to user)

After the loop exits, output a single summary. This is the only user-facing output during the run — no per-finding narration while looping.

```markdown
## Auto-review-plan complete

**Target:** IMPLEMENTATION_PLAN_checkout-redesign.md
**Rounds:** 2 (converged) | **Final verdict:** Ready to implement

**Auto-applied (2):**
- Phase 2 — Rollout: added rollback step (finding: no-rollback-plan)
- Phase 3 — Migration: added failure-mode bullet (finding: unspecified-failure-mode)

**Flagged for approval (2):**

1. **[Blocking] Clarify success criteria** — `Goals` section
   Review finding: "Success" is defined as "users like the new checkout" — no measurable target.
   Why flagged: requires product-level decision (target metric, threshold, time window).
   To apply: update the Goals section with a specific metric, then re-run auto-review-plan or proceed.

2. **[Watch] Long-term coupling risk** — `Phase 4 — Cleanup`
   Review finding: cleanup phase leaves the legacy checkout module wired to the new pricing service.
   Why flagged: advisory — may be acceptable depending on deprecation timeline.
   To apply: decide whether to decouple now or track as post-launch debt.

**Oscillations caught:** 0
**Edit failures:** 0

Log: `.claude/auto-review-plan-log.md`

Next: resolve the flagged items above. Re-run `/auto-review-plan` if you make non-trivial edits, then hand the plan to implementation.
```

For in-conversation targets, append the final revised plan text under a `### Revised plan` heading in the summary so the user can paste it back into plan mode or use it directly.

## Invoking the sub-skill

This skill orchestrates `review-plan` only. For each round, invoke `review-plan` with the current plan (path for file-based targets, inline text for in-conversation targets — the sub-skill handles both) and apply its output per the policy above. Do not re-implement `review-plan`'s delegation to `senior-engineer` and `product-manager` — call the skill and consume its structured output.

## User override mid-run

If the user interrupts mid-round with a correction (e.g., "don't touch the Goals section", "flag everything in Phase 3, even small edits"), honor it for the remainder of the run, note it in the log, and continue.

## Related skills

- **review-plan** — the single-shot version; this skill is a loop around it
- **auto-review** — the code-side analog; same loop pattern for `review-code` + `simplify`
- **plan-implementation** / **plan-refactor** — create the plan this skill hardens
- **grill-me** — use *before* the plan is written for upfront clarification

# Bot-miss audit — 2026-06

What `/review-code` and `/simplify-code` missed that an AI review bot (greptile,
coderabbit, cursor/bugbot, qodo) then caught on a `sontek` PR and that the author
**addressed**. Author runs both skills before every PR, so each entry here is a
genuine miss by the shipped reviewer rubric — the raw material for the
"prove-the-gap-first" loop the detection suite already uses (see `evals/README.md`,
"Rules added from real bot findings").

Scope: 35 PRs across `stacklet/platform` (Python) and `stacklet/platform-ui`
(TypeScript/React), 2026-05 → 2026-06. ~53 valid-addressed misses after filtering
nits and false positives.

## Root cause (the headline)

~40 of the 53 misses are **cross-path invariants, not local bugs**. The flagged
line read as correct in isolation; the defect lived in the *relationship* between
the changed hunk and a sibling branch, a fallback path, or a downstream function the
diff fed into. The reviewers read the diff hunk locally; these invariants span
hunks. Almost every gap below is a facet of that one root cause.

## Gap table (valid-addressed only)

| # | Gap | ~n | Owner | Status | Representative PRs |
|---|---|---|---|---|---|
| 1 | **Sibling-branch divergence** — a field/guard/special-case/output honored on one of several co-present branches handling the same concept, dropped on a parallel one (bar-vs-line renderer, happy-vs-fallback, retry-vs-original, sibling recipe) | ~15 | code-reviewer | **no rule** | platform-ui#3100, #3120; platform#3769, #3810, #3802, #3739 |
| 2 | **Fallback / failure / null-input path** — the unreviewed path drops data or crashes (formatter throws, Zod `.default` rejects explicit `null`, error boundary loses content, `new Date(true)` passes a NaN guard) | ~8 | code-reviewer | partial | platform-ui#3117, #3120, #3098; platform#3784, #3774 |
| 3 | **SQL/structured content in LLM prompt strings** — scalar subquery on non-unique key, mismatched time window, Azure `COALESCE` undercount, join-first vs MATERIALIZED, prompt example contradicting its own rule, dual-purpose schema-field description | ~9 | sql-reviewer / none | **no rule (surface uncovered)** | platform#3785, #3732, #3801, #3731 |
| 4a | **Retry/timeout budget** — per-attempt vs whole-call budget, missing budget-derived timeout, liveness bound omits a backoff term | ~4 | review-perf / code-reviewer | **existing `deadline_before_handoff` under-generalized** | platform#3769, #3762, #3774 |
| 4b | **First-record schema inference** | ~1 | code-reviewer | **existing `first_record_schema` missed it** | platform#3793 |
| 4c | **Cleanup skipped by non-local exit (shell)** | ~1 | code-reviewer | **existing `cleanup_nonlocal_exit` is Py/Go/TS-only** | platform#3818 |
| 5 | **Config default violates the change's own safety constraint** — ALB idle-timeout default below the SQL ceiling; worker clamp ordering | ~3 | code-reviewer / iac | no rule | platform#3769, #3818 |
| 6 | **Theme-migration completeness / WCAG contrast** (FE) — background semanticized, foreground left hardcoded; shallow-merge clobbers nested style | ~4 | code-reviewer | no rule (niche) | platform-ui#3128 |
| 7 | **Type-coercion / lenient-parser edge** — `?? 0` turns missing into zero, `Intl` percent default truncates | ~3 | code-reviewer | partial | platform-ui#3098, #3100 |

## Prioritized plan

Each gap goes through the same loop, validated twice: (1) a unit detection eval —
sanitized `catch_/safe_` fixtures + an honest `.old.md` baseline, A/B proves the
specific rule beats the generic baseline without new false positives; (2) a real-PR
sanity check — run the live `code-reviewer` on the actual bot-reviewed commit in the
local checkout, rule-off vs rule-on, expecting red→green. A gap that doesn't
discriminate is dropped as churn (the `log_assertion` / `type_dispatch` precedent).

1. **Gap 1 — sibling-branch divergence.** First: most frequent, generalized across
   Python + TypeScript + shell, cleanest expression of the root cause. New rule in
   `code-reviewer.md`.
2. **Gap 2 — fallback/null-path correctness.**
3. **Gap 4a/4b/4c — widen the three existing rules** that already exist but missed
   real instances (cheapest wins; add these shapes as fixtures + generalize wording).
4. **Gap 3 — SQL-in-prompt-strings.** New lane; bigger design question (a reviewer
   that lints SQL embedded in string literals, and prompt-example-vs-rule contradiction).
5. **Gaps 5–7** deferred (lower frequency / niche).

## Reproducibility ledger

Real-PR sanity runs use the bot comment's `original_commit_id` (the buggy state the
bot reviewed) in the local checkouts at `~/code/stacklet/{platform,platform-ui}`.
Commit SHAs are resolved at sanity-check time from the GitHub review-comment API and
recorded per gap as it's worked.

- Gap 1: platform-ui#3100 `ChartElement.tsx` — cursor[bot] "Line chart ignores
  `spec.stacked` unlike bar chart", bot-reviewed commit **`27f632dfe2bb`**
  (`LineChartBody` :270 hardcodes `stacked:false`; `BarChartBody` :194 honors
  `spec.stacked` — siblings ~75 lines apart).

## Gap 1 result (rule: `sibling_branch_divergence`)

**Status: shipped. Gated end-to-end at faithful (branch) scope; unit fixtures are an FP/regression guard, not the gate.**

The gate is scope-sensitive, and finding that out was the main lesson:

- **Unit eval (single snippet): no discrimination.** Generic "check consistency"
  baseline and the specific rule both pass. A 12-line snippet with the two siblings
  adjacent is trivially solvable — the single-snippet harness structurally can't
  reproduce the real difficulty (siblings far apart in a large diff). So the unit
  cases are kept only as a fire-check + the scatter FP guard, not as the gate.
- **Paths mode (whole file in scope): misleading.** With the entire 280-line
  `ChartElement.tsx` in scope, OFF *catches* the parity class (it flagged
  `bar-axis-ignores-xtype`, `line-yscale-min-0-clips-negatives` unprompted) — so
  paths mode understates the gap. An early single-slug grep here nearly produced a
  false "discriminates" call; the fix was to dump all finding slugs and measure the
  class, not one slug.
- **Branch mode on the real 33-file / 3,745-line PR diff (the faithful miss
  condition): clean discrimination.** This is how the PR was actually reviewed.
  - **OFF: 0/3** — across 3 runs the live reviewer found other real bugs and **zero
    parity findings at all** (slug-verified, not a grep artifact). Reviewing the
    real diff, the cross-branch comparison never happens.
  - **ON (tightened procedural "build a parity table" wording): 3/3** — caught
    `line-chart-ignores-stacked` / `line-stacked-hardcoded` every run, plus
    `bar-axis-ignores-x` (a second real divergence), with no parity false positives.

Two methodology notes worth keeping: (1) for cross-path bugs, the single-snippet
unit harness is the wrong instrument — the faithful **branch-scope** end-to-end is
the gate. (2) The first prose wording fired inconsistently end-to-end (paths 2/3);
rewording it as an explicit **procedure** (enumerate branches → fill a parity table
→ flag the blank cell) made firing reproducible (branch 3/3). Detection must be
class-level over N runs, never a single slug in a single run.

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
| 3 | **SQL/structured content in LLM prompt strings** — scalar subquery on non-unique key, mismatched time window, Azure `COALESCE` undercount, join-first vs MATERIALIZED, prompt example contradicting its own rule, dual-purpose schema-field description | ~9 | sql-reviewer / none | **REFUTED — already covered** (see Gap 3 result) | platform#3785, #3732, #3801, #3731 |
| 4a | **Retry/timeout budget** — per-attempt vs whole-call budget, missing budget-derived timeout, liveness bound omits a backoff term | ~4 | review-perf / code-reviewer | **existing `deadline_before_handoff` under-generalized** | platform#3769, #3762, #3774 |
| 4b | **First-record schema inference** | ~1 | code-reviewer | **existing `first_record_schema` missed it** | platform#3793 |
| 4c | **Cleanup skipped by non-local exit (shell)** | ~1 | code-reviewer | **existing `cleanup_nonlocal_exit` is Py/Go/TS-only** | platform#3818 |
| 5 | **A change violates a constraint documented elsewhere in the same file** — config default below the SQL ceiling; worker clamp ordering; **a new branch under a set-membership guard inheriting suffixes the guard's comment forbids (platform#3832)** | ~4 | code-reviewer / iac | **CONFIRMED — omnibus stuck ~1/3 any wording; focused lane 3/3 (see Gap 5 result)** | platform#3769, #3818, **#3832** |
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

## Gap 2 result (rule: `default_ignores_explicit_null`)

Shipped. A fallback that fills *absent* but not *explicit null* (Zod `.default()`,
Python `dict.get(k, d)`). Unit-churn like Gap 1; gated end-to-end where the base
reviewer **confidently mis-cleared** the hazard ("null resilience is sound") 3/3 and
the rule flipped it to a correctly-hedged flag 3/3. Proven cross-language (a Go
`comma-ok` map fallback is caught), and a verdict-leak in the safe fixtures (a
"CLEAN" comment) was found to mask a Haiku FP — fixed by exempting null-checked
results in the gate, and a `tests.gen.js` guard now fails CI on any fixture that
echoes the verdict.

## Gap 4 result (widen existing rules — 1 of 3)

Prove-the-gap-first showed only one of the three "missed" rules had a real wording
gap. **`deadline_before_handoff`** was widened to cover a retry loop that re-applies
the whole-call budget per attempt (the queue/handoff shape was the only one it
named); retry fixture CLEAN→FLAGGED, 7/7 both models, with an absolute-deadline
exemption added to clear a Haiku FP the broad wording briefly caused.
**`cleanup_nonlocal_exit`** already generalizes to a shell `exit` between
acquire/release (8/8, shell fixtures kept as proof) and **`first_record_schema`**
already covers its shape — both production misses were diff-scale, so no reword
(forcing one would be churn).

## Gap 3 result (SQL/structured content in prompts — REFUTED)

No rule. Prove-the-gap-first refuted the whole lane. Running the live `code-reviewer`
on the real #3785 diff (`4c2e5f71`, base `bdc172971`) caught **both** facets 3/3 with
no rule added:

- **SQL correctness in the prompt example** — flagged the scalar subquery on the
  non-unique `account_id` as a P2; the reasoning *beat the bot's*, citing the actual
  ORM unique index (`ix_account_id__provider_account_id`), explaining the
  "more than one row" error, and proposing the `IN (...)` fix that matches the
  prompt's own plural "resolve the matching ids" prose.
- **Example contradicts its own rule** — flagged that the new aggregate-first
  `MATERIALIZED` directive is counter-demonstrated by un-rewritten join-first
  examples in the same prompt.

So the biggest "new lane" in this audit was not a coverage gap: the reviewer already
treats prompt-embedded SQL and prompt rule/example consistency as reviewable code.
The bots' wild catches were diff-scale/situational or predate reviewer improvements.
Same call as the over-fit audit's refuted hypotheses — do not build what the reviewer
already does. (`#3801` mismatched-XML-tags and `#3731` schema-field-description are
single-instance facets not separately pursued.)

## Gap 5 result (new code path violates a documented constraint — CONFIRMED, and NOT fixable by an omnibus rule)

A facet of Gap 5, from a later PR: **platform#3832** (`s3proxy.py`, bot-reviewed
commit `5cfc64a4`, base `4bfc15a5`). The diff adds a presigned-URL redirect *inside*
the pre-existing `if Path(key).suffix in (".html",".css",".js",".json",".woff2")`
block whose unchanged header comment says those suffixes "can never be served via
pre-signed URLs" (breaks relative links; CORS for `.json`/`.woff2`). The new branch
gates on `COMPONENT=="docs"` and size but **not** suffix, so it inherits the whole
set — only `.js` is actually safe. coderabbit flagged it 🟠 Major.

This one **breaks the "just reword it as a procedure" playbook that fixed Gap 1**, and
that is the finding. Evidence ladder (rule = `documented_constraint_violated`):

- **Omnibus reviewer, end-to-end on the real diff — stuck at ~1/3 regardless of
  wording.** Five wordings × 3 runs each (18 runs): OFF 1/3, one-line bullet 0/3,
  full investigation-step 1/3, mechanical set-membership grep + structural gate 1/3,
  **mandatory triage gate 0/3** (the most imperative wording did *worst* — three runs
  silently ignored the "mandatory" instruction). Every run that caught it
  independently rated it **P3-latent** ("only the `.js` bundle is >1 MB today, so the
  `.json`/`.woff2` case isn't reachable") — a defensible call; coderabbit's Major
  over-stated it, and coderabbit's own fix (`allow .js + .css`) was wrong since the
  comment forbids `.css` too. The author shipped the correct `.js`-only narrowing.
- **Unit harness (single snippet): no discrimination — both 5/5.** Live rule *and*
  the honest one-sentence generic baseline (`*.old.md`) both pass 5/5 (3 catch + 2
  safe, Opus-4.8 notemp). As with Gaps 1/2 the snippet is a fire-check + FP guard, not
  a gate — here it also proved the knowledge is fully present.
- **Focused single-purpose lane, end-to-end on the real diff: 3/3.** A lane given
  *only* this one check (the lean wording, nothing else) flagged it every run, quoted
  the unchanged constraint, named the affected members, **refused the "not produced
  today" dismissal**, and gave the `.js` fix. Severities medium/high/medium.

So the lever is **focus, not wording**. The bug is non-salient (a 15-line "done-looking"
feature add; the governing comment sits *outside* the diff hunk), and on a tiny diff the
omnibus reviewer spends its attention on the salient, concrete finding (a missing test)
and trades this away — *no rubric wording changes that*. This is the boundary of the
Gap-1 lesson: for sibling-divergence the ON rule lifted end-to-end (0/3→3/3) because
that PR was 33 files full of co-present branches (high salience); here the ON rule does
not lift (1/3→1/3) because the check is non-salient and the constraint is out-of-hunk.
A dedicated lane is the only thing that reaches it.

Decision: **confirmed gap, do NOT record as refuted, and do NOT ship as an omnibus
bullet** (as an omnibus bullet it is churn — 1/3 = baseline). The lean rule + fixtures
are kept as the **seed and regression set for a focused "cross-region consistency"
lane** (proposed below). "Less wording is better" is now measured, not asserted: the
one-line bullet matched the multi-paragraph step end-to-end, and the longest wording
was the worst.

### Methodology refinements this produced

1. **The unit-isolation refutation bar is unsafe for attention-class misses.** In
   isolation both baseline and rule score 5/5 on a bug the omnibus misses 2/3 of the
   time — isolation cannot reproduce an attention failure. (Cross-checked: **Gap 3's
   refutation is still sound** — it was decided on the *live reviewer, real diff, 3/3*,
   not in isolation. The flaw is specifically isolation- or single-run-based refutation.)
2. **The discrimination gate must be N runs of the live reviewer on the real,
   non-salient diff** — and even that only tells you whether an *omnibus* rule helps.
   A "no-lift" result there does not mean "no gap"; it can mean "needs a lane."
3. **New lever for the cross-region family: a focused lane.** When wording can't lift
   the omnibus, isolate the check.

### Lanes built and gated — one ships, one held

The "~40 of 53 misses are cross-path" headline splits into two directions, so we built a
focused lane for each and gated both end-to-end on the real diff (the inward bug at
platform#3832; a constructed compiler-invisible wire-key rename for the outward case).

- **`context-consistency-reviewer` (inward — SHIPS).** Consolidates the cross-region
  family — `documented_constraint_violated` (new path vs enclosing guard), `sibling_branch_divergence`,
  `stale_latest_state`, new-instance-vs-siblings, `comment_contradicts_code`, removed-guard
  (2d) — into one single-purpose lane. Gate on #3832: omnibus **1/3** (18 runs, any
  wording) → lane **3/3 at P2**; FP control (the fixed `.js`-only commit) **0/3 false
  positives** (2/3 fully clean, 1/3 a legitimate P3 that the now-stale block comment
  overclaims). Wired into `review-code` always-dispatch.
- **`blast-radius-reviewer` (outward — HELD; its one real gap folded into step-2 instead).**
  Built on disk, not wired. Three end-to-end attempts to find a blast-radius bug the omnibus
  misses all failed — the omnibus caught each whenever the diff carried *any* signal: a
  salient wire-key rename **2/2 (P0)**, and a seconds→ms unit change with a param rename
  **3/3 (P0)**. Its step-2 blast-radius trace is strong; a standalone lane is churn on every
  reproducible case (same verdict as Gap 3 and the rename above). **But the unit eval found
  one genuine gap — a *concept* gap, not an attention gap.** Lane 2's `blast_radius` fixtures
  (producer + stale consumer in one snippet) run against the *real pre-change step-2 wording*
  scored **3/5**: it missed the two **semantic-drift** catches (a value's unit changed
  seconds→ms; a list's sortedness guarantee dropped) — the class with *no token to grep*,
  which step-2's trigger list (renamed/removed/literal/signature/exception) never named.
  Adding a **semantic-drift bullet to step-2** ("a meaning change behind a stable signature
  — unit/sign/sortedness/tz/nullability; no token to grep, so diff the behavior and check
  every caller's assumption") takes it to **5/5**, no FP on the safe cases. So lane 2's only
  distinct value shipped — as four lines in the omnibus's step-2, not a new always-on lane.
  Revisit a standalone lane only if a *non-salient* blast-radius miss is ever found that the
  live omnibus fails over N runs.

**Attention gap vs concept gap — the second deciding variable.** The inward lane and the
blast-radius concept failed the omnibus for *different* reasons, and the reason dictates the
fix. The inward family is an **attention** gap: the omnibus *has* the concept but loses it on
a small diff, so no rule wording lifted it (1/3 across 18 runs) and only a focused **lane**
did (3/3). Semantic drift is a **concept** gap: step-2 simply never named the class, but the
omnibus engages blast-radius readily once anything triggers it (3/3 end-to-end), so the fix is
**wording** (name the concept in step-2), not a lane — and a unit A/B is enough to gate a
concept gap (5/5 vs 3/5), whereas an attention gap needs the faithful end-to-end. Diagnose
which before choosing lane-vs-wording: does the omnibus *know* this class (attention → lane)
or *not* (concept → wording)?

**The deciding variable is salience, and it sharpens every refutation in this doc.** A
cross-region miss needs a focused lane only when it is *non-salient* — buried in a
done-looking diff with the governing context out of the hunk (inward #3832). When the
issue is the diff's obvious focus (a rename; a prompt-engineering PR's SQL — Gap 3), the
omnibus reliably catches it and a lane is churn. So "does a lane help?" reduces to "is
this miss salient in its real diff?" — measured by N runs of the live omnibus on that
diff, never in isolation.

## Audit status

Real rules shipped: **`sibling_branch_divergence`** (Gap 1), **`default_ignores_explicit_null`**
(Gap 2), **`deadline_before_handoff`** widened (Gap 4a). Refuted as already-covered:
Gap 3, Gap 4b/4c. **Confirmed but not omnibus-fixable:** Gap 5
(`documented_constraint_violated`, platform#3832) — the omnibus reviewer is stuck at
~1/3 regardless of wording, a focused lane hits 3/3; the lean rule + fixtures are the
seed for a proposed cross-region consistency lane (see Gap 5 result). The recurring
lesson stands but now has a sharper edge: the live reviewer is stronger than the raw
bot-miss list implies, so each gap must be proven against the live reviewer on the real
diff over N runs — and a no-lift result there means "needs a lane," not "no gap"
(unit-isolation and single-run refutations are unsafe for attention-class misses).
Remaining un-screened: rest of Gap 5 (config/IaC facets), Gap 6 (FE theme/contrast),
Gap 7 (type-coercion edges) — lower frequency; screen the same way before building.

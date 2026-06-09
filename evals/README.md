# Detection-rule evals

A small [promptfoo](https://promptfoo.dev) suite that regression-tests the
detection rules in our review skills (`code-reviewer`, `perf-reviewer`,
`gha-security-reviewer`, …) and guards against **over-fitting** — a rule whose
trigger is bound to the surface form of one bug instead of the invariant the bug
violates, so it fires on the case the author pictured and silently misses the
rest of the class.

Each rule is tested with **paired fixtures across languages**:

- `catch_*` — code that violates the rule's invariant. The rule **must** fire.
  Several are written in forms (a different API, a different language) an
  over-fit rule would miss — they are the proof the wording generalized.
- `safe_*` — code that trips the rule's surface tokens but is genuinely fine
  (usually the rule's own validation-gate exemption). The rule **must not** fire.

A rule is well-generalized when **every** `catch_*` across Python / Go / TS flags
and **every** `safe_*` stays clean.

## The suite tests the LIVE rules, not copies

The `current` rule wording is **sliced straight out of the live agent files** at
generate time (`tests.gen.js` + `rules/sources.json`) — there is no copy to
drift. Editing a rule in `plugins/sontek-skills/agents/*.md` and re-running the
suite immediately reflects the change. That is what makes the before/after
workflow below trustworthy: you are measuring the shipped text.

## Layout

```
evals/
  promptfooconfig.yaml     # providers (bedrock default + anthropic), prompt, tests
  prompt.js                # builds the chat prompt in plain JS (no Nunjucks, so
                           #   fixtures with ${{ }} / {{ }} survive verbatim)
  tests.gen.js             # globs fixtures/ -> one test per file; slices the
                           #   live rule text per rules/sources.json
  rules/
    sources.json           # rule -> {live agent file, start/end slice anchors}
    <rule>.old.md          # frozen pre-generalization wording (the A/B "before")
  fixtures/
    <rule>/<language>/<catch|safe>_<name>.<ext>
```

Adding a fixture is just dropping a file — no config edit:

- top dir under `fixtures/` = the rule (must have a `rules/sources.json` entry)
- sub dir = language (`python` | `go` | `typescript` | `gha`)
- filename prefix = expectation (`catch_` → `FLAGGED`, `safe_` → `CLEAN`)

## Run it

Driven by [`just`](https://just.systems) from the **repo root**. Requires
[`mise`](https://mise.jdx.dev) (pins Node via `.mise.toml`); the recipes install
the rest.

```bash
just              # list recipes
just gen          # sanity-check the generator (no tokens)
just show         # print the live rule text the suite will use
just eval         # run the suite on Bedrock (default provider)
just eval anthropic   # run it on the Anthropic API instead
just view         # open the result grid (filter by rule / language / verdict)
just validate     # parse config + load prompt/generator, no API calls
```

### Provider & credentials

Recipes default to **Bedrock** and use the standard AWS credential chain
(env vars / `AWS_PROFILE` / SSO / instance role) — **no `ANTHROPIC_API_KEY`
needed**. Override the model/region without editing any file:

```bash
export EVAL_BEDROCK_MODEL=us.anthropic.claude-opus-4-...   # your inference-profile id
export AWS_REGION=us-east-1
just eval
```

`just eval anthropic` switches to the Anthropic API (needs `ANTHROPIC_API_KEY`).
The default Bedrock model id in `promptfooconfig.yaml` is a **placeholder** —
set `EVAL_BEDROCK_MODEL` to your account's Opus inference-profile id.

> **Node version:** promptfoo (pinned to the latest, `0.121.15`) declares
> `engines ^20.20.0 || >=22.22.0`. `.mise.toml` at the repo root pins Node
> `24.15.0`, and every recipe runs through `mise exec`, so the right Node is used
> regardless of your shell — install [mise](https://mise.jdx.dev) and the
> recipes handle the rest (`mise install` runs as part of `_ensure`).

The suite is small (~36 cases) at `temperature: 0`, cheap enough to gate in CI.
Assertions are deterministic `contains` checks on a `VERDICT: FLAGGED|CLEAN`
line — no LLM grader by default.

## Prove a generalization helps: baseline → edit → re-run

Because `current` reads the **live** rules, the suite measures the real before
and after of a rule change:

```bash
just eval                 # BASELINE — the shipped rules as they are today
# ... edit the rule in plugins/sontek-skills/agents/<agent>.md ...
just eval                 # AFTER — the same fixtures against your edit
```

promptfoo saves every run; `just view` shows the history so you can compare the
two grids side by side. A generalization "helped" when `catch_*` cases that were
RED go GREEN **and** no `safe_*` case flips RED (no new false positives).

There is also a **durable** before/after baked into the repo via the frozen
`*.old.md` snapshots:

```bash
just eval-old             # "before": the frozen over-fit wording
just eval                 # "after":  the live wording
just ab                   # both, back to back
```

### Baseline run (Opus-4.8 + Haiku-4.5 on Bedrock)

The suite was run on the live wording across both models, then the over-fit
`*.old.md` wording for the A/B. What the data showed — and what we did about it:

| Rule | `old` (over-fit) | `current` (live) | Outcome |
|---|---|---|---|
| `cleanup_nonlocal_exit` | Opus 4/6 · Haiku 4/6 | **6/6 both** | generalized step-2f wording **validated** (old missed Go `defer` / asyncio) |
| `blocking_io_async` | (no snapshot) | was Opus **4/5** (TS miss) | **fixed** — perf-reviewer P1 made language-agnostic → 5/5 both |
| `gha_with_injection` | Opus 2/3 · Haiku 2/3 | Opus 3/3, **Haiku 2/3** | **fixed** — `with:`/`github-script` carve-out → 3/3 both |
| `log_assertion` | **8/8 both** | 8/8 both | both models bridge the `caplog.text` over-fit → generalization **dropped** (churn) |
| `type_dispatch` | **7/7 both** | 7/7 both | both bridge the `isinstance` over-fit → **dropped** (churn) |
| `path_traversal` | Opus 6/7 · Haiku 7/7 | **7/7 both** | live already general → no change |

After the two fixes (`blocking_io_async`, `gha_with_injection`), the full suite is
**36/36 on both Opus-4.8 and Haiku-4.5**. The eval refuted two of the audit's
top-priority generalizations (they were churn on every model tested) and surfaced
the `blocking_io` gap the audit had missed — which is the whole reason it exists.

To reproduce the before/after for the fixed rules: `just eval-old` (frozen
over-fit) vs `just eval` (live). The `log_assertion`/`type_dispatch` `.old.md`
snapshots are kept as a standing guard against re-introducing over-fit wording,
even though those rules need no change today.

### Rules added from real bot findings (prove-the-gap-first)

A later pass mined AI-review-bot comments on merged `stacklet/platform` PRs for
issues `/review-code` missed, then **proved each gap before writing a rule**: fetch
the exact commit the bot reviewed, run our reviewer on that real file, and only
add a rule when it demonstrably misses. Six hypotheses, four confirmed:

| Hypothesis | Verdict | Rule |
|---|---|---|
| stale shared "latest" state written by some paths | **confirmed miss** → fixed | `stale_latest_state` |
| deadline/timeout computed before a thread-pool queue | **confirmed miss** → fixed | `deadline_before_handoff` |
| schema/columns inferred from the first record | **confirmed miss** → fixed | `first_record_schema` |
| sort/compare keyed on a non-finite float (NaN) | **confirmed miss** → fixed | `nonfinite_sort_key` |
| prompt instruction/example contradiction | refuted (reviewer caught it) | none |
| eval asserts liveness not the graded dimension | refuted (by-design / caught) | none |

Each confirmed rule is validated **twice**: the unit fixtures here (26 cases,
green on Opus-4.8 and Haiku-4.5), and an end-to-end re-run of the full reviewer
on the original buggy file — red before the rule, green after. `nonfinite_sort_key`
carries an FP-weighted safe set (plain finite-float sorts must stay clean); both
models hold that line. The two refutations are the point: they stopped rules we
didn't need, the same way the over-fit audit's `log_assertion`/`type_dispatch`
were dropped.

### Code-quality rules added from a slop-audit tool (prove-the-discrimination-first)

A third pass mined the lanes of an external "slop audit" tool (cognitive
complexity, size/sprawl, structural duplication, dead code) for code-quality
dimensions our `code-simplifier` had no fire-able rule for. Four new rules landed
in `code-simplifier.md`; each carries a `*.old.md` snapshot of the **honest
pre-rule guidance** (the generic clarity/abstraction prose that predated it), so
`just ab` measures whether the *specific* rule beats the generic baseline — the
churn bar that dropped `log_assertion`/`type_dispatch`.

The discrimination is engineered into **boundary safe cases**, not the catches:
a cohesive `coverages/tasks.py` vs a heterogeneous `tasks.py` (same shape, one
keys on subsystem-heterogeneity); an irreducible resource-scope nest vs reducible
guard-clause nesting; a framework-discovered `Command` vs a dead class. A rule
"earns its place" only when the generic baseline mishandles a boundary case the
specific rule gets right.

| Rule | generic baseline (old) | live rule (current) | discriminates on |
|---|---|---|---|
| `inline_data_blob` | Opus **3/5** · Haiku 5/5 | **5/5 both** | Opus — generic won't "move data out" of a view from "reduce complexity" |
| `reducible_complexity` | Opus **4/6** · Haiku **5/6** | **6/6 both** | both — generic FPs irreducible resource-scopes / misses flat branch-density |
| `dead_code_unused_abstraction` | Opus 6/6 · Haiku **4/6** | **6/6 both** | Haiku — generic misses test-only abstractions |
| `god_module` | Opus 6/6 · Haiku **3/6** | **6/6 both** | Haiku — generic FPs the API router + cohesive tasks, misses heterogeneous tasks |

Full suite after this pass: **92/92 on both Opus-4.8 and Haiku-4.5**. (This pass
also tightened `comments_over_explanatory` with a hard citation gate — a comment
anchored to an incident/bug id is load-bearing, return CLEAN — which closed two
long-standing Haiku safe-case FPs without losing any catch.) Run the A/B on Opus
with `just ab-notemp` (Opus 4.6+ rejects the `temperature` field — see the
`*-notemp` recipes). A fifth change — widening
`structure.duplicate-function-signatures` to compare against pre-existing siblings
and hoist to an existing base class — is not unit-testable in this single-snippet
harness. A behavioral two-file test (a new detector duplicating a *committed*
sibling not in the diff) confirmed the live skill **does** flag the duplication and
name the out-of-diff sibling — but the base model with no plugin does the same on a
small diff, so the behavior **does not discriminate** from baseline and earns no
behavioral gate (the same drop-non-discriminating rationale as the over-fit audit).
The widening stays as an explicit cue for the focused structure lane, where the
payoff is attention at diff scale that a small fixture can't measure; treat it as
verified-to-fire, not independently gated.

### Review lenses pulled from an external PR-review toolkit (prove-the-gap-first)

A later pass mined an external PR-review toolkit's specialist agents for review
*lenses* `code-reviewer` lacked, then gated each one the usual way — a `catch`
that the *faithful* prior wording misses and the new rule catches, on both models.
Two of three candidates landed:

| Rule | faithful baseline (old) | live rule (current) | discriminates on |
|---|---|---|---|
| `comment_contradicts_code` | 3/6 both | **6/6 both** | both — baseline *sees* the lie but its gate only fired on a grown surface, so it returned CLEAN |
| `type_invariant_enforcement` | 5/7 both | **7/7 both** | both — baseline misses a constructible-invalid instance (no constructor check, public mutable) |

The third candidate, `silent_failure_extras` (over-broad catch scope; production
fallback to fake data), was **dropped as churn**: its faithful baseline is the
existing fail-fast rules ("best effort silent recovery," "returning fallbacks"),
and a capable model already flags those shapes from them (Haiku 6/6, Opus 5/6 — a
~1/12 delta). Same call as `log_assertion` / `type_dispatch`.

One methodology note worth keeping: `type_invariant` first read as *no* discrimination
(7/7 baseline) until the baseline was corrected — the first `.old.md` had been seeded
with the rule's own concept ("make invalid states unrepresentable"), wording
code-reviewer never actually shipped. A baseline that quietly contains the answer
hides a real gap. The `.old.md` must be what the skill *truly said before*, nothing more.

### Cross-path rules need a faithful end-to-end gate, not the unit harness (`sibling_branch_divergence`)

A 2026-06 audit of AI-bot comments on merged `sontek` PRs (catalogued in
[`bot-miss-audit-2026-06.md`](bot-miss-audit-2026-06.md)) found the dominant
`/review-code` miss was **cross-path**: a field/guard one of several co-present
sibling branches carries but a peer drops (bar renderer reads `spec.stacked`, line
renderer hardcodes it; chart path attaches `y_format`, table fallback drops it). The
new `sibling_branch_divergence` rule addresses it, and proving it exposed a gating
lesson:

- **Unit suite (single snippet): does NOT discriminate** — generic "check
  consistency" guidance catches two adjacent siblings just as well. The unit cases
  here are a fire-check + the scatter **FP guard** (a renderer that legitimately has
  no stacking concept must stay CLEAN — Opus & Haiku both hold it), *not* the gate.
- **Faithful end-to-end (live `code-reviewer`, branch mode on the real 33-file PR
  diff) IS the gate:** OFF flagged zero parity findings across 3 runs; ON caught the
  divergence 3/3. Paths mode (whole file in scope) masked the gap — it must be the
  branch-scope diff to reproduce the real miss.
- Two process notes: measure the **finding class over N runs**, never one slug in
  one run (a single-slug grep nearly produced a false "discriminates"); and phrase a
  cross-path rule as an explicit **procedure** ("enumerate branches → parity table →
  flag the blank cell"), which turned inconsistent firing (2/3) reproducible (3/3).

### A default that fills absent-but-not-explicit-null (`default_ignores_explicit_null`)

From the same bot-miss audit: a reviewer cleared `z.array(...).default([])` on a
resume frame as "null-resilient," but `.default()` replaces only `undefined`, so an
explicit wire `null` throws and drops the whole restored conversation (Python's
`dict.get(k, fallback)` has the identical absent-vs-present-null gap). The rule
names the absent-only fallback shapes and gates on **reachability** — flag only when
the source can actually send explicit `null`.

Gating mirrored `sibling_branch_divergence`:

- **Unit suite: does NOT discriminate.** A generic "handle nulls" baseline catches
  the `.default([])` / `.get()` cases just as well once the snippet annotates the
  field as nullable right beside the fallback. Unit cases are a fire-check + the
  **reachability FP guard** (a `.default()` on a field that is only ever *omitted*,
  never null, must stay CLEAN — holds on Opus & Haiku), not the gate.
- **Faithful end-to-end IS the gate, and the reachability gate is the point.** On
  the real PR diff the base reviewer **confidently mis-cleared** the hazard ("null
  resilience is sound") 3/3; with the rule it flagged it 3/3 — and *correctly
  conditionalized* on the unknown backend fact ("fires only if the backend emits
  `elements: null`; confirm against the serializer; the zod mechanism is certain
  regardless"). The rule's value is flipping a confident wrong-clear into a
  correctly-hedged flag that asks the author the right question, not asserting an
  unverifiable consequence.
- **Not over-fit to the two repo idioms.** The rule names Zod `.default()` and
  Python `.get()` (what the repo uses), so a Go fixture was added to check it didn't
  bind to those tokens: a `val, ok := m[key]` map fallback that fills absent-only is
  flagged on both models, its nil-checked sibling stays clean. The model generalizes
  from the invariant, not the named idioms.
- **A verdict-leak in the safe fixtures was masking a real false positive.** The
  safe-case comments originally said "CLEAN," echoing the output verdict. Removing
  that exposed a Haiku false positive on a `.get()` result that *was* correctly
  null-checked (`is not None`). The fix was to make the validation gate explicitly
  exempt a subsequently null-checked result; both models then hold 7/7. Lesson:
  never let a fixture comment state the verdict — it silently props up the FP guard.

### Widening existing rules that missed real instances (prove-the-gap, 1 of 3)

The audit also flagged three *existing* rules that a bot caught a case our reviewer
missed (`deadline_before_handoff`, `cleanup_nonlocal_exit`, `first_record_schema`).
Reconstructing each missed shape as a fixture and running the **live** rule showed
only one was an actual wording gap — the other two already generalize, so their
production misses were diff-scale, not fixable by rewording (forcing a change would
be churn):

- **`deadline_before_handoff` — widened.** It covered a timeout that ignores a
  queue/handoff wait, but missed the sibling shape: a **retry loop that re-applies
  the whole-call budget per attempt** (N attempts × full timeout). The retry fixture
  was CLEAN under the old wording on both models; widening the rule to name both
  shapes of the one invariant ("a per-unit timeout that ignores time already
  consumed — by a wait *or* by prior attempts") flips it to FLAGGED 7/7. A Haiku
  regression surfaced mid-A/B — the broad wording briefly flagged a *correct* retry
  loop that shares one **absolute** deadline — and was closed by adding that
  absolute-deadline pattern to the validation gate.
- **`cleanup_nonlocal_exit` — no change, already general.** A shell recipe that
  `exit`s between `deps-up` and `deps-down` (leaking the stack) is FLAGGED 8/8 and
  the `trap`-guarded version stays CLEAN, even though the rule's examples are all
  code-level (lock/event/await). Shell fixtures kept as standing proof.
- **`first_record_schema` — no change.** Its existing fixtures already encode the
  first-element-derivation shape the bot caught; the production miss was diff-scale.

## Provenance

Fixtures are clean, self-contained reconstructions of bug *shapes* — no
proprietary code is copied. Several shapes came from real `stacklet/platform`
PRs where an AI review bot caught something `/review-code` did not:

- `cleanup_nonlocal_exit` — PR #3806 (`asyncio.Event` not unset when the create
  call fails).
- `blocking_io_async` — PR #3774 (sync `_materialize_user_sql` called inside an
  `async` handler; fixed with `asyncio.to_thread`).

The repo is Python-only, so the Go and TypeScript variants are deliberate ports
of those Python shapes: porting the *invariant* into other languages is how we
prove a rule generalizes instead of memorizing one stack's idiom.

## Adding a rule

1. Add a `rules/sources.json` entry pointing at the live bullet/section in its
   agent file (`start`/`end` anchor lines — keep them stable across rewordings).
2. Add `fixtures/<rule>/<lang>/catch_*.ext` in **at least two languages**, each
   in a form a token-keyed version of the rule would miss.
3. Add `fixtures/<rule>/<lang>/safe_*.ext` that trips the surface tokens but hits
   the validation gate.
4. (Optional) Add `rules/<rule>.old.md` to A/B against wording you're replacing.
5. `just gen` to confirm the cases are picked up, `just show` to confirm the
   slice binds to the right live text, then `just eval`.

**Never state the verdict in a fixture.** Describe what the code *does* ("scatter
has no stacking concept"), never the answer the model should reach — no "CLEAN",
"FLAGGED", "must not flag", or "this is a bug" in a comment or docstring. A fixture
that names its own verdict lets the model copy it instead of reasoning, which
silently props up the safe-case false-positive guard and can hide a real over-flag.
`just gen` enforces this: it fails on any fixture containing the verbatim verdict
tokens `CLEAN` / `FLAGGED` (the same check runs in CI).

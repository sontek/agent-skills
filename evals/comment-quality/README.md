# Comment-quality evals

A promptfoo A/B that measures whether an edit to review-pr's
[`comment-style.md`](../../plugins/sontek-skills/skills/review-pr/references/comment-style.md)
**changes the comment that actually gets written** — and changes it for the
better — rather than just reading well as guidance.

This is a *different axis* from the sibling [detection suite](../README.md). That
one asks "given a code snippet, does the rule fire?" (`FLAGGED`/`CLEAN`). This one
asks the model to **write the PR comment** it would post for a finding, then grades
that comment. Detection suite = finder wording; this suite = comment wording.

## What it tests

Each scenario in `scenarios/` is a coalesced finding plus the code context the
comment will anchor to. The model writes one comment under the `comment-style`
guidance, and the asserts grade it:

- **`asserts/hygiene.js`** — deterministic, no grader: rejects em/en-dashes, a
  `--` used as a dash, and label prefixes (`blocking —`, `P1`, …). This is the
  review-tone mechanical rule, checked on the actual output.
- **llm-rubric (per scenario)** — the property the edit is supposed to produce.
  For the mismatch scenarios that is: *does the comment say which side of the
  mismatch is correct and which one should change, instead of describing the
  discrepancy neutrally?*

## The A/B axis (same pattern as the detection suite)

- `current` (default) reads the **live** `comment-style.md` from the skill. No
  copy to drift — edit the live reference, re-run, the suite reflects it.
- `RULE_VARIANT=old` reads the frozen pre-edit snapshot in
  `variants/comment-style.baseline.md` — the honest "before".

An edit **helped** when a mismatch scenario the `old` baseline gets wrong goes
right under `current`, **and** the `control` scenario stays right under both (no
regression).

```bash
just gen-cq            # generate + list cases, no tokens
just show-cq           # which guidance file binds for each variant
just validate-cq       # promptfoo loads prompt.js + tests.gen.js, no API calls
just ab-cq             # old (before) then current (after), back to back
just eval-cq           # just the current (after) wording
just eval-cq anthropic # against the Anthropic API instead of Bedrock
```

## Overfit guard (the methodology this repo holds itself to)

A rule that only fires on the exact case that motivated it has learned the
surface, not the invariant. Three guards are built into the scenario set:

- **Both mismatch directions.** `01`/`02` are *code-right* (the doc/docstring is
  stale); `03` is *doc-right* (the code is the bug). A rule that just learned
  "blame the doc" passes `01`/`02` and **fails `03`**. The edit must make the
  comment name whichever side is actually correct.
- **Held-out shapes.** `05` (help text vs a changed default, code-right) and `06`
  (a `-> int` annotation vs a bytes-returning body, doc-right) are forms the rule
  text was *not* written against. They test generalization: the cue should fix a
  new shape, not just the four it was tuned on. `06` on Opus does exactly that
  (0→3).
- **A non-mismatch control.** `04` is a plain null-deref finding. Both variants
  should pass it; if `current` fails the control, the edit degraded ordinary
  comments and hasn't earned its place.
- **A second, independent property.** `01` also carries the observable-effect-
  over-mechanism rubric (edit #4), which can prove out as **churn** — the baseline
  already says "plain words" / "describe the code that's there" and may already
  satisfy it. If `old` and `current` both pass that rubric, drop edit #4 the same
  way `log_assertion` / `type_dispatch` were dropped from the detection suite.

## Measured result (Opus 4.1 + Haiku 4.5, Bedrock, repeat 3)

The "name which side is right" edit (`comment-style.md`) **discriminates**. With
neutral findings (the finding states the two facts but NOT which side is right),
the baseline hedges with "which one is correct?" and the edit makes the comment
commit to the side that drifted:

| scenario | opus.old | opus.cur | haiku.old | haiku.cur | |
|---|---|---|---|---|---|
| doc_vs_code_statuscode | 3/3 | 3/3 | **0/3** | **3/3** | +1 |
| docstring_vs_code | **0/3** | **3/3** | **0/3** | **3/3** | +2 |
| spec_vs_code_bug | **0/3** | **3/3** | **0/3** | **3/3** | +2 |
| helptext_vs_default (held-out) | 3/3 | 3/3 | 3/3 | 3/3 | = |
| type_contract_vs_impl (held-out) | **0/3** | **3/3** | 3/3 | 3/3 | +1 |
| control_plain_finding | 3/3 | 3/3 | 3/3 | 3/3 | = |

**6 wins, 0 regressions.** Every baseline-failing cell flipped to passing, the
control held, and a held-out doc-right shape the cue was *not* tuned against
(`type_contract_vs_impl`, opus 0→3) was fixed too — evidence the rule generalizes
rather than memorizing the four cases it was written from.

Getting here took two corrections the eval forced, which are the point of having it:

- **The first scenario draft showed false churn.** Findings that pre-stated the
  verdict ("the documented contract is the intended behavior") let the model copy
  the answer, so baseline and edit both passed — no headroom. Rewriting the
  findings to be *neutral* exposed the real gap.
- **The eval refuted the first fix and validated the second.** A clause that said
  "infer the side when context tells you, and reserve an open question for genuine
  ambiguity" *regressed* `docstring/opus` and `spec/haiku` (3→0): the "reserve an
  open question" escape hatch licensed more hedging. Replacing it with a directional
  rule — *a contract/spec is authoritative over violating code; a deliberate change
  is authoritative over an unupdated doc; don't punt with "which is correct?"* — and
  no escape hatch is what produced the clean 6/0.

Not gated cleanly:
- **The observable-effect rubric (#4)** is too noisy to call: the Haiku grader
  returned a self-contradictory verdict (its reason said the comment *did* lead
  with the observable effect, then failed it). Kept as guidance, not claimed as a
  measured gate.

## Reproduce

The provider id template `{{ env.EVAL_BEDROCK_MODEL or '...' }}` only renders when
the env var is **set** — the `or 'default'` fallback comes through literally and
Bedrock rejects it. So both must be exported:

```bash
export AWS_PROFILE=<profile> AWS_REGION=us-east-1
export EVAL_BEDROCK_MODEL=us.anthropic.claude-opus-4-1-20250805-v1:0
export EVAL_BEDROCK_GRADER=us.anthropic.claude-haiku-4-5-20251001-v1:0
just ab-cq            # baseline (frozen) then live, back to back
```

Run with the Haiku id as `EVAL_BEDROCK_MODEL` for the weaker-model arm; the
`--repeat 3` is passed by re-running, or add it to the recipe. Scenarios are clean
reconstructions of bug *shapes*; no proprietary code is copied.

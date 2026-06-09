# Behavioral skill tests

A small harness that runs a skill **end-to-end** through headless `claude -p` and
checks that it **discriminates** from a baseline — i.e. the skill (or a skill edit)
measurably changes what Claude does.

This complements `evals/` (promptfoo). The two cover different surfaces:

| | promptfoo (`just eval`) | behavioral (`just behavioral`) |
|---|---|---|
| Tests | detection-rule wording | whole-skill behavior, end-to-end |
| Input | a static code snippet | a real task + fixture repo |
| Signal | FLAGGED / CLEAN | did the skill change behavior vs baseline |
| Speed / cost | fast, cheap, deterministic-ish | slow, **spends tokens**, noisy |
| Good for | review/finder rules | triggering, procedure, output-shaping skills |

Use behavioral tests only for what promptfoo can't reach. A behavioral pass is
weaker evidence than a promptfoo pass — treat it as a discrimination signal, not a
correctness oracle.

## The core idea: discrimination

A test is useful only if it has **discriminating power** — it gets one result with
the skill behavior present and a *different* result with it absent. A test that
passes (or fails) regardless of the skill is measuring the base model, not the
skill, and proves nothing. Every spec is therefore a two-arm A/B:

- **skill on/off** — e.g. `commit`: on = our plugin loaded, off = no plugin. The
  base default adds a `Co-Authored-By` trailer; our skill suppresses it.
- **edit before/after** — e.g. `clarify-probe`: on = a plugin copy *with* the
  candidate edit, off = the current plugin *without* it. Proves whether a proposed
  skill edit is gate-able (and, as a bonus, that the edit works).

The runner runs each arm `--runs N` times and only reports **DISCRIMINATES** when
every on-run matches `expect_on` and every off-run matches `expect_off`.

## Running

```bash
just behavioral list                 # show specs
just behavioral run                   # all specs, 2 runs/arm
just behavioral run commit            # one spec
just behavioral run --runs 3 --keep   # more reps; keep temp dirs to inspect
```

`just behavioral` → `uv run --no-project python -m behavioral` (stdlib only, no
deps). Requires the `claude` CLI on PATH and `git`.

### Permissions

The harness spawns nested `claude -p --dangerously-skip-permissions` (a headless
run hangs otherwise). The auto-mode classifier blocks that unless pre-authorized,
so `.claude/settings.local.json` (gitignored) allows `Bash(just behavioral:*)`.
The nested spawn lives *inside* the Python subprocess, so only the top-level
`just` call is gated.

## Adding a spec

Specs are declarative — add a `TestSpec` to `SPECS` in `specs.py`:

```python
"my-spec": TestSpec(
    name="my-spec",
    doc="one-line description",
    setup=setup_empty_repo,                 # build the fixture repo
    prop=lambda t, proj: ...,               # observable behavior -> bool
    prop_desc="what the property checks",
    arm_on=Arm("on",  "<prompt>", plugin=PLUGIN_DIR, disable_global=True),
    arm_off=Arm("off", "<prompt>", plugin=None,      disable_global=True),
    expect_on=True, expect_off=False,
)
```

`prop` reads the `Transcript` (`.text`, `.tools_used`, `.skills_fired`,
`.skill_fired(name)`, `.available_skills`) and/or the project dir (e.g. the
resulting commit message). For an edit-gate, give the on-arm an `edit={...}` (path
→ appended text) instead of a plugin; `harness.edited_plugin` builds the copy.

## Hard-won constraints (don't regress these)

Building a *valid* harness defeated several confounds. Each silently corrupts
results if ignored:

1. **Write the transcript outside the project dir.** A skill may run
   `git checkout`/`clean`/`bisect`, clobbering an in-repo transcript mid-write.
2. **The globally-installed plugin is a cached copy and loads without
   `--plugin-dir`.** To control which version runs, `disable_global=True`
   (`--settings` flag precedence) and `--plugin-dir` the version under test.
   Otherwise an edit-gate compares the edited copy against itself.
3. **Pick opposite-of-default behaviors.** `git bisect` failed as a spec because
   the base model already bisects — no delta to measure. Good props are things the
   base model does the *other* way by default (attribution trailer, em-dashes,
   naming conventions, a specific probe question).
4. **Headless under-triggers vs interactive.** Natural-language triggering is
   unreliable in `claude -p` (a skill that auto-fires interactively may not here).
   Force-invoke the skill ("Use the X skill to …") to test the skill *body*
   separately from triggering.
5. **No `grep -q` downstream of a pipe under `set -o pipefail`** (the original bash
   version): grep exits on first match, SIGPIPEs the producer, and pipefail
   surfaces that as a spurious failure. (Avoided entirely now that parsing is
   Python.)

## Current specs

- **`commit`** (skill on/off) — *proven.* Skill suppresses the `Co-Authored-By`
  trailer and enforces conventional-commit format; base default does neither.
  Discriminates 2/2.
- **`clarify-probe`** (edit before/after) — *proven.* Adding the want/should-want
  probe makes Claude ask *"if you didn't have to justify this… what would you
  actually want?"* on a sophistication-signaling prompt; current clarify doesn't.
  Discriminates 2/2.
- **`simplify-fanout`** (skill on/off) — *proven.* simplify-code dispatches ≥4
  read-only code-simplifier lane sub-agents; the base model (no plugin) edits
  directly and dispatches none. Discriminates 2/2.

### review-pr reviewer-roster guards

These four caught a real drift: review-pr's reviewer-selection table had fallen
behind review-code's — it omitted the `perf-reviewer`, `iac-reviewer`, and
`sql-reviewer` rows and the post-coalesce recall gap-sweep. Each was first run as
an **edit before/after** A/B (off = the live skill *without* the rule = the red
baseline; on = the same skill *plus* the rule) and **discriminated 2/2** — in every
case the live skill *fired* but dispatched the specialist zero times, and the model
did **not** reach for the agent on its own, refuting the churn hypothesis the way
the over-fit audit refuted `log_assertion` / `type_dispatch`. The rules now ship in
`review-pr/SKILL.md`, so these are **single-arm regression guards against the live
skill** (re-verified green 2/2 on the shipped table-row / coalesce wording, which is
terser than the probe that proved the mechanism — proving the probe worked is not
proving the shipped form works):

- **`review-pr-iac`** — Terraform-only diff → `iac-reviewer` dispatched. 2/2.
- **`review-pr-sql`** — raw-SQL (sqlalchemy `text(`) diff → `sql-reviewer` dispatched. 2/2.
- **`review-pr-perf`** — non-Django FastAPI diff → `perf-reviewer` dispatched. 2/2.
- **`review-pr-gapsweep`** — a *second* `code-reviewer` runs after coalesce as a
  recall sweep (≥2 dispatches vs 1). Unlike the roster rows this was a deliberate
  product call, not pure drift: propose-only review-pr is precision-biased, and the
  sweep is a recall lever — adopted because its downstream `finding-verifier` +
  value-triage filter the extra candidates before they reach a comment. 2/2.

The prompt for all four is deliberately neutral — it never names Terraform, IaC,
SQL, perf, or any reviewer — so reviewer selection is driven by the skill text, not
the prompt. That neutrality is what makes the discrimination honest.

### review-code DRY-extraction guards

A follow-up moved the reviewer-selection table out of both skills' bodies into one
shared `review-code/references/reviewer-selection.md` that both read, so the roster
can't drift again (the root-cause fix for the drift above). The risk of that
extraction is behavioral: does the model still *load* the reference and select
correctly, rather than dispatching only the always-on pair? Three single-arm guards
against the live `review-code` confirm it does, mirroring the review-pr fixtures
(review-code's `branch` mode diffs the same range):

- **`review-code-iac`** — Terraform diff → `iac-reviewer` dispatched. 2/2.
- **`review-code-sql`** — raw-SQL diff → `sql-reviewer` dispatched. 2/2.
- **`review-code-perf`** — FastAPI diff → `perf-reviewer` dispatched. 2/2.

Together with the re-run review-pr guards (also 2/2 post-extraction), this proves
both skills still select every specialist through the shared reference.

### review-design

- **`review-design`** (skill on/off) — *proven, 3/3.* The new `review-design` skill
  routes a module through the `senior-engineer` judgment agent — the first wiring of
  senior-engineer to code scope (it was plan-only). ON (plugin loaded) dispatches
  senior-engineer over the module; OFF (no plugin) the base model reviews the module
  inline and dispatches no judgment agent. Smoke-level discrimination, same class as
  `simplify-fanout`: it proves the skill does the new thing (route code to
  senior-engineer), not that the verdict is correct.

  *Methodology note the eval forced:* the first cut used a leading prompt
  ("...dispatching the judgment agent(s) it selects") and **failed to discriminate**
  — the no-skill OFF arm improvised its own senior-engineer dispatch (OFF 1/2).
  Stripping the prompt to the bare "review the design of src/billing" — so only the
  skill body, not the prompt, can cause a dispatch — produced a clean 3/3 both arms.
  Same lesson as the roster guards: the prompt must not do the skill's job.

### Designed, not yet implemented

- **`fence`** (code-simplifier, edit before/after) — does adding a
  Chesterton's-fence guard stop the simplifier from deleting code that looks dead
  but is load-bearing? Needs a bespoke fixture (a file with a plausibly-removable
  but actually-depended-on line carrying an in-code signal) and a `prop` that
  checks the line survives. Follows the same `edit=` pattern as `clarify-probe`.

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

### Designed, not yet implemented

- **`fence`** (code-simplifier, edit before/after) — does adding a
  Chesterton's-fence guard stop the simplifier from deleting code that looks dead
  but is load-bearing? Needs a bespoke fixture (a file with a plausibly-removable
  but actually-depended-on line carrying an in-code signal) and a `prop` that
  checks the line survives. Follows the same `edit=` pattern as `clarify-probe`.

"""Declarative behavioral test specs + the discrimination runner.

A spec is a two-arm A/B: run the SAME task with the skill behavior present
(`arm_on`) and absent (`arm_off`), check an observable `prop`, and require the
result to differ as expected. If both arms land the same way, the harness has no
discriminating power for that property — the base model already does (or never
does) the thing, so the skill can't be credited.

Two arm shapes:
  * skill on/off  (e.g. `commit`): on = live plugin, off = no plugin.
  * edit before/after (e.g. `clarify-probe`): on = plugin copy WITH the candidate
    edit, off = current plugin WITHOUT it. Both disable the global cached copy so
    only the version under test is loaded.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .harness import PLUGIN_DIR, Transcript, edited_plugin, run_claude


# --- fixtures / property helpers --------------------------------------------
def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    ).stdout

def _init_repo(proj: Path) -> None:
    proj.mkdir(parents=True, exist_ok=True)
    _git(proj, "init", "-q")
    _git(proj, "config", "user.email", "t@t.t")
    _git(proj, "config", "user.name", "t")

def setup_staged_change(proj: Path) -> None:
    """A repo with a baseline commit and one staged change to be committed."""
    _init_repo(proj)
    (proj / "app.py").write_text('print("v1")\n')
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "baseline")
    (proj / "app.py").write_text('print("v2")\nprint("added a line")\n')
    _git(proj, "add", "-A")

def setup_empty_repo(proj: Path) -> None:
    _init_repo(proj)
    _git(proj, "commit", "-q", "--allow-empty", "-m", "init")

_TRAILER = re.compile(r"Co-Authored-By|Generated with|🤖", re.I)

def prop_commit_clean(t: Transcript, proj: Path) -> bool:
    """True iff a NEW commit was made and its message has no attribution trailer."""
    msg = _git(proj, "log", "-1", "--format=%B").strip()
    if not msg or msg == "baseline":
        return False  # model didn't commit
    return not _TRAILER.search(msg)

def evidence_commit(t: Transcript, proj: Path) -> str:
    return "HEAD msg: " + _git(proj, "log", "-1", "--format=%s").strip()

_PROBE = re.compile(r"didn.t have to justify|what would you actually want", re.I)

def prop_probe_asked(t: Transcript, proj: Path) -> bool:
    return bool(_PROBE.search(t.text))

def evidence_probe(t: Transcript, proj: Path) -> str:
    return "clarify fired" if t.skill_fired("clarify") else "clarify NOT fired"


# --- arm + spec types --------------------------------------------------------
@dataclass
class Arm:
    label: str
    prompt: str
    plugin: Path | None = PLUGIN_DIR  # dir to --plugin-dir, or None for no plugin
    disable_global: bool = True       # force the globally-installed cached copy off
    # edit applied to a plugin copy at runtime; when set, `plugin` is ignored and
    # a fresh edited copy is built (path -> appended text).
    edit: dict | None = None

@dataclass
class TestSpec:
    name: str
    doc: str
    setup: Callable[[Path], None]
    prop: Callable[[Transcript, Path], bool]
    prop_desc: str
    arm_on: Arm
    arm_off: Arm | None = None  # None => single-arm assertion against the live skill
    expect_on: bool = True
    expect_off: bool = False
    max_turns: int = 5
    evidence: Callable[[Transcript, Path], str] | None = None


# Prompt that hands clarify a sophistication-signaling request (the trigger for
# the want/should-want probe). Shared so the regression guard and any future
# A/B use identical wording.
_CLARIFY_SIGNALING_PROMPT = (
    "Use the clarify skill to interview me about this: I want to build an API. "
    "Make it really scalable, clean, and modern."
)


# --- the registry ------------------------------------------------------------
SPECS: dict[str, TestSpec] = {
    # PROVEN: skill suppresses the attribution trailer; base default adds it.
    "commit": TestSpec(
        name="commit",
        doc="commit skill suppresses the Co-Authored-By trailer (skill on vs off)",
        setup=setup_staged_change,
        prop=prop_commit_clean,
        prop_desc="commit message has NO attribution trailer",
        arm_on=Arm("skill-ON",
                   "Use the commit skill to commit the staged change with an appropriate conventional-commit message.",
                   plugin=PLUGIN_DIR, disable_global=True),
        arm_off=Arm("skill-OFF",
                    "Commit the staged change with an appropriate commit message.",
                    plugin=None, disable_global=True),
        expect_on=True, expect_off=False,
    ),
    # Single-arm assertion against the LIVE clarify skill: on a signaling prompt,
    # clarify must ask the want/should-want probe. RED until the probe ships in
    # clarify/SKILL.md; GREEN after — and a regression guard if it's ever removed.
    # (The base/current skill scores False, so this test has teeth — confirmed by
    # the discrimination A/B before this was simplified to single-arm.)
    "clarify-probe": TestSpec(
        name="clarify-probe",
        doc="live clarify asks the want/should-want probe on a signaling prompt",
        setup=setup_empty_repo,
        prop=prop_probe_asked,
        prop_desc="model asks the want/should-want probe",
        arm_on=Arm("live-clarify", _CLARIFY_SIGNALING_PROMPT,
                   plugin=PLUGIN_DIR, disable_global=True),
        arm_off=None,  # single-arm assertion against the live skill
        expect_on=True,
        max_turns=2,
        evidence=evidence_probe,
    ),
}


# --- runner ------------------------------------------------------------------
def _run_arm(spec: TestSpec, arm: Arm, work: Path) -> tuple[bool, str, Transcript]:
    proj = work / "project"
    spec.setup(proj)
    plugin = arm.plugin
    if arm.edit is not None:
        plugin = edited_plugin(arm.edit, work / "edited")
    t = run_claude(arm.prompt, proj, max_turns=spec.max_turns,
                   plugin=plugin, disable_global=arm.disable_global, out_dir=work / "out")
    val = spec.prop(t, proj)
    ev = spec.evidence(t, proj) if spec.evidence else evidence_commit(t, proj)
    return val, ev, t


def run_spec(spec: TestSpec, runs: int, work_root: Path) -> bool:
    print(f"=== {spec.name}: {spec.doc} ===")
    if spec.arm_off is None:
        # Single-arm assertion against the live skill: pass iff every run matches.
        print(f"    assert: {spec.prop_desc}  (expect {spec.expect_on})")
        ok = 0
        for i in range(1, runs + 1):
            val, ev, _ = _run_arm(spec, spec.arm_on, work_root / f"{spec.name}-{i}")
            mark = "PASS" if val == spec.expect_on else "FAIL"
            print(f"    run {i}:  {spec.arm_on.label}={val} [{mark}] ({ev})")
            ok += val == spec.expect_on
        passed = ok == runs
        print(f"    --- {ok}/{runs} matched  =>  {'PASS' if passed else 'FAIL'}\n")
        return passed

    print(f"    property: {spec.prop_desc}  (expect ON={spec.expect_on}, OFF={spec.expect_off})")
    on_ok = off_ok = 0
    for i in range(1, runs + 1):
        on_val, on_ev, _ = _run_arm(spec, spec.arm_on, work_root / f"{spec.name}-on-{i}")
        off_val, off_ev, _ = _run_arm(spec, spec.arm_off, work_root / f"{spec.name}-off-{i}")
        on_mark = "ok" if on_val == spec.expect_on else "XX"
        off_mark = "ok" if off_val == spec.expect_off else "XX"
        print(f"    run {i}:  {spec.arm_on.label}={on_val} [{on_mark}] ({on_ev})   "
              f"{spec.arm_off.label}={off_val} [{off_mark}] ({off_ev})")
        on_ok += on_val == spec.expect_on
        off_ok += off_val == spec.expect_off
    discriminates = (
        spec.expect_on != spec.expect_off and on_ok == runs and off_ok == runs
    )
    verdict = "DISCRIMINATES — gate-able" if discriminates else "NO clear discrimination"
    print(f"    --- ON matched {on_ok}/{runs}, OFF matched {off_ok}/{runs}  =>  {verdict}\n")
    return discriminates

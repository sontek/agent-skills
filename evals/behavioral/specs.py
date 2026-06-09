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

def setup_slop_repo(proj: Path) -> None:
    """A repo with staged, multi-lane AI slop for the deslop fan-out to chew on.

    Spans every lane so each one has a file to gate on: a heterogeneous tasks
    module (complexity/god-module), a test-only abstraction (structure/dead-code),
    deep nesting (complexity), a scaffolding comment (comments), and a swallowing
    try/except (defensive).
    """
    _init_repo(proj)
    (proj / "README.md").write_text("# app\n")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "baseline")
    (proj / "src").mkdir()
    (proj / "tests").mkdir()
    (proj / "src" / "tasks.py").write_text(
        '''from celery import shared_task


@shared_task
def sync_github_pull_requests(repo_id):
    GitHubProvider(repo_id).sync_open_pulls()


@shared_task
def reconcile_stripe_subscription(org_id):
    stripe.Subscription.retrieve(org_id)


@shared_task
def send_welcome_email(user_id):
    mailer.send(to=user_id, template="welcome")


@shared_task
def export_audit_csv(org_id):
    storage.save(f"audit/{org_id}.csv", _to_csv(org_id))
'''
    )
    (proj / "src" / "command_router.py").write_text(
        '''from dataclasses import dataclass


@dataclass
class ParsedCommand:
    name: str
    args: list


class CommandRouter:
    def route(self, raw):
        name, *args = raw.lstrip("/").split()
        return ParsedCommand(name=name, args=args)
'''
    )
    (proj / "tests" / "test_command_router.py").write_text(
        '''from src.command_router import CommandRouter


def test_route():
    assert CommandRouter().route("/x a").name == "x"
'''
    )
    (proj / "src" / "views.py").write_text(
        '''import json


def list_open_prs(repo, since):
    out = []
    for page in repo.paginate("/pulls"):
        for pr in page:
            if pr["state"] == "open":
                if pr.get("user"):
                    if pr.get("created_at"):
                        if pr["created_at"] >= since:
                            out.append(pr["number"])
    return out


def load_config(path):
    # TODO: implement more validation here
    try:
        return json.load(open(path))
    except Exception as e:
        print(e)
        return {}
'''
    )
    _git(proj, "add", "-A")

def setup_terraform_pr_repo(proj: Path) -> None:
    """A feature branch whose ONLY changed file vs main is Terraform.

    review-pr's local-branch mode diffs ``<base=main>...HEAD``; the sole changed
    file is IaC, so a correct reviewer-selection step must add ``iac-reviewer``.
    The current review-pr reviewer table omits an IaC row entirely (review-code
    has one; review-pr drifted), so the live skill should NOT dispatch it — that
    omission is the gap this spec measures.
    """
    _init_repo(proj)
    (proj / "README.md").write_text("# infra\n")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "baseline")
    _git(proj, "branch", "-M", "main")
    _git(proj, "checkout", "-q", "-b", "feature/add-bucket")
    (proj / "main.tf").write_text(
        '''resource "aws_s3_bucket" "exports" {
  bucket = "company-customer-exports"
  acl    = "public-read"
}

resource "aws_security_group" "db" {
  name = "db-sg"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
'''
    )
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "add s3 bucket and db security group")

def _feature_branch_with(proj: Path, rel: str, body: str, msg: str) -> None:
    """main baseline + a feature branch whose only changed file vs main is `rel`."""
    _init_repo(proj)
    (proj / "README.md").write_text("# app\n")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "baseline")
    _git(proj, "branch", "-M", "main")
    _git(proj, "checkout", "-q", "-b", "feature/change")
    path = proj / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", msg)

def setup_rawsql_pr_repo(proj: Path) -> None:
    """Feature branch whose only change is non-Django raw SQL — sql-reviewer's domain.

    `import sqlalchemy` + `text(` matches review-code's DB-layer selection signal;
    review-pr's table has no DB row, so the live skill should not select sql-reviewer.
    """
    _feature_branch_with(proj, "reports.py", '''import sqlalchemy as sa


def search_orders(conn, customer_name):
    query = sa.text(f"SELECT * FROM orders WHERE customer = '{customer_name}'")
    return conn.execute(query).fetchall()
''', "add order search query")

def setup_apptier_pr_repo(proj: Path) -> None:
    """Feature branch whose only change is non-Django app-tier code — perf-reviewer's domain.

    A FastAPI handler with a per-item synchronous network round-trip on an async
    path matches review-code's application-tier selection signal; review-pr's table
    has no app-tier row (only django-perf), so the live skill should not select
    perf-reviewer.
    """
    _feature_branch_with(proj, "api.py", '''import httpx
from fastapi import FastAPI

app = FastAPI()


@app.get("/orgs/{org_id}/users")
async def enriched_users(org_id: str):
    users = await fetch_users(org_id)
    out = []
    for user in users:
        profile = httpx.get(f"https://profiles.internal/{user['id']}").json()
        out.append({**user, "profile": profile})
    return out
''', "add enriched users endpoint")

def setup_smalldiff_pr_repo(proj: Path) -> None:
    """Feature branch with one small, real defect — fodder for the recall gap-sweep.

    A tiny diff keeps the initial fan-out fast enough to reach the post-coalesce
    sweep inside the run budget; the unguarded divide gives the pipeline a finding
    to coalesce so the sweep is clearly warranted.
    """
    _feature_branch_with(proj, "calc.py", '''def average(values):
    return sum(values) / len(values)
''', "add average helper")

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

def _lane_dispatches(t: Transcript) -> int:
    """Count read-only code-simplifier lane sub-agents the fan-out dispatched.

    The runtime exposes the sub-agent tool as `Agent` (older runtimes: `Task`);
    match either, and only count dispatches whose subagent_type is code-simplifier.
    """
    n = 0
    for e in t.events:
        if e.get("type") != "assistant":
            continue
        for b in e.get("message", {}).get("content", []) or []:
            if b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"):
                st = (b.get("input", {}) or {}).get("subagent_type", "") or ""
                if "code-simplifier" in st:
                    n += 1
    return n

def prop_fanned_out(t: Transcript, proj: Path) -> bool:
    return _lane_dispatches(t) >= 4

def evidence_fanout(t: Transcript, proj: Path) -> str:
    return (f"{_lane_dispatches(t)} code-simplifier lane agents; "
            f"simplify-code fired={t.skill_fired('simplify-code')}")

def _subagent_dispatches(t: Transcript, needle: str) -> int:
    """Count fan-out sub-agents whose subagent_type contains ``needle``.

    Same shape as `_lane_dispatches`, generalized to any reviewer name so an
    orchestration spec can assert a specific specialist was selected.
    """
    n = 0
    for e in t.events:
        if e.get("type") != "assistant":
            continue
        for b in e.get("message", {}).get("content", []) or []:
            if b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"):
                st = (b.get("input", {}) or {}).get("subagent_type", "") or ""
                if needle in st:
                    n += 1
    return n

def _reviewer_prop(needle: str):
    return lambda t, proj: _subagent_dispatches(t, needle) >= 1

def _reviewer_evidence(needle: str):
    return lambda t, proj: (f"{needle} dispatches={_subagent_dispatches(t, needle)}; "
                            f"review-pr fired={t.skill_fired('review-pr')}")

prop_iac_reviewer_dispatched = _reviewer_prop("iac-reviewer")
evidence_iac = _reviewer_evidence("iac-reviewer")
prop_sql_reviewer_dispatched = _reviewer_prop("sql-reviewer")
evidence_sql = _reviewer_evidence("sql-reviewer")
prop_perf_reviewer_dispatched = _reviewer_prop("perf-reviewer")
evidence_perf = _reviewer_evidence("perf-reviewer")

def prop_gapsweep(t: Transcript, proj: Path) -> bool:
    """The recall sweep dispatches a SECOND code-reviewer after coalesce."""
    return _subagent_dispatches(t, "code-reviewer") >= 2

def evidence_gapsweep(t: Transcript, proj: Path) -> str:
    return (f"code-reviewer dispatches={_subagent_dispatches(t, 'code-reviewer')}; "
            f"review-pr fired={t.skill_fired('review-pr')}")


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

# Force-invoke simplify-code on the slop repo (headless under-triggers natural
# language, so name the skill — we're testing the fan-out body, not triggering).
_SIMPLIFY_PROMPT = (
    "Use the simplify-code skill to review and clean up the staged changes in "
    "this repository. Follow the skill's process exactly."
)

# Force-invoke review-pr on the Terraform branch. Deliberately NEUTRAL: it never
# names Terraform, IaC, or any reviewer — so whether iac-reviewer gets dispatched
# is driven by the skill's reviewer-selection step, not the prompt. "Stop once
# you've gathered the findings" keeps it off the approval gate and inside the turn
# budget (we only need the dispatch, not posted comments).
_REVIEW_PR_PROMPT = (
    "Use the review-pr skill to review the changes on this branch against the "
    "main branch. Follow the skill's process exactly, including dispatching the "
    "reviewer sub-agents it selects. Stop once you've gathered the findings — you "
    "do not need to present or post anything."
)

# The roster rows (iac / sql / perf) and the recall gap-sweep that the edit-A/Bs
# proved out now ship in review-pr's SKILL.md, so all four specs are single-arm
# guards against the live skill — no edit constants needed.


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
    # PROVEN (smoke): simplify-code fans out to read-only code-simplifier lane
    # detectives. ON (plugin loaded) dispatches >=4 lane sub-agents; OFF (no
    # plugin) the base model edits directly and dispatches none. Guards against
    # the fan-out silently regressing to a single agent.
    "simplify-fanout": TestSpec(
        name="simplify-fanout",
        doc="simplify-code fans out to >=4 read-only code-simplifier lane detectives (skill on vs off)",
        setup=setup_slop_repo,
        prop=prop_fanned_out,
        prop_desc=">=4 code-simplifier lane sub-agents dispatched",
        arm_on=Arm("skill-ON", _SIMPLIFY_PROMPT, plugin=PLUGIN_DIR, disable_global=True),
        arm_off=Arm("skill-OFF", _SIMPLIFY_PROMPT, plugin=None, disable_global=True),
        expect_on=True, expect_off=False,
        max_turns=10,
        evidence=evidence_fanout,
    ),
    # Reviewer-roster drift, now FIXED in review-pr's step-2 table. Each of the
    # three below was first run as an edit before/after A/B (OFF = current live
    # review-pr without the row = RED baseline; ON = same skill + the selection
    # rule) and discriminated 2/2 — the live skill fired but dispatched the
    # specialist zero times, and the model did NOT reach for the agent on its own
    # (refuting the churn hypothesis the way log_assertion / type_dispatch were
    # refuted). With the rows now shipped, these are single-arm guards against the
    # LIVE skill: GREEN today, RED if a row is ever removed. The edit constants are
    # gone with the A/B — the shipped table-row wording is what the guard measures.
    "review-pr-iac": TestSpec(
        name="review-pr-iac",
        doc="live review-pr dispatches iac-reviewer on a Terraform-only diff (regression guard)",
        setup=setup_terraform_pr_repo,
        prop=prop_iac_reviewer_dispatched,
        prop_desc="iac-reviewer sub-agent dispatched",
        arm_on=Arm("live-review-pr", _REVIEW_PR_PROMPT,
                   plugin=PLUGIN_DIR, disable_global=True),
        arm_off=None,  # single-arm guard; IaC-row edit A/B proved discrimination 2/2 first
        expect_on=True,
        max_turns=12,
        evidence=evidence_iac,
    ),
    "review-pr-sql": TestSpec(
        name="review-pr-sql",
        doc="live review-pr dispatches sql-reviewer on a raw-SQL diff (regression guard)",
        setup=setup_rawsql_pr_repo,
        prop=prop_sql_reviewer_dispatched,
        prop_desc="sql-reviewer sub-agent dispatched",
        arm_on=Arm("live-review-pr", _REVIEW_PR_PROMPT,
                   plugin=PLUGIN_DIR, disable_global=True),
        arm_off=None,  # single-arm guard; DB-layer-row edit A/B proved discrimination 2/2 first
        expect_on=True,
        max_turns=12,
        evidence=evidence_sql,
    ),
    "review-pr-perf": TestSpec(
        name="review-pr-perf",
        doc="live review-pr dispatches perf-reviewer on a FastAPI diff (regression guard)",
        setup=setup_apptier_pr_repo,
        prop=prop_perf_reviewer_dispatched,
        prop_desc="perf-reviewer sub-agent dispatched",
        arm_on=Arm("live-review-pr", _REVIEW_PR_PROMPT,
                   plugin=PLUGIN_DIR, disable_global=True),
        arm_off=None,  # single-arm guard; app-tier-row edit A/B proved discrimination 2/2 first
        expect_on=True,
        max_turns=12,
        evidence=evidence_perf,
    ),
    # Recall gap-sweep, now SHIPPED in review-pr's coalesce. Not pure roster drift —
    # propose-only review-pr is precision-biased, so adopting a recall sweep was a
    # deliberate product call (its downstream finding-verifier + value-triage filter
    # the extra candidates). The edit before/after proved the lever 2/2 (2 vs 1
    # code-reviewer dispatches); now a single-arm guard against the live skill. Prop
    # counts a SECOND code-reviewer dispatch (initial fan-out + sweep).
    "review-pr-gapsweep": TestSpec(
        name="review-pr-gapsweep",
        doc="live review-pr runs a second code-reviewer recall sweep after coalesce (regression guard)",
        setup=setup_smalldiff_pr_repo,
        prop=prop_gapsweep,
        prop_desc=">=2 code-reviewer dispatches (initial + recall sweep)",
        arm_on=Arm("live-review-pr", _REVIEW_PR_PROMPT,
                   plugin=PLUGIN_DIR, disable_global=True),
        arm_off=None,  # single-arm guard; gap-sweep edit A/B proved discrimination 2/2 first
        expect_on=True,
        max_turns=20,
        evidence=evidence_gapsweep,
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

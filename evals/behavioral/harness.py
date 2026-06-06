"""Behavioral skill-test harness — run skills end-to-end via headless `claude -p`.

Unlike the promptfoo suite (which scores detection-rule FLAGGED/CLEAN on a static
snippet), this runs a skill through the real CLI and inspects the transcript: which
skill fired, what the model did, what landed in the output. Its job is
*discrimination* — show that a skill (or a skill edit) changes behavior vs. a
baseline. A test with no discriminating power measures the base model, not the skill.

Hard-won constraints baked in here (see README):
  * Transcript is written OUTSIDE the project dir — a skill may run git checkout/
    clean/bisect and clobber an in-repo file mid-write.
  * The globally-installed plugin is a CACHED COPY, and is loaded even without
    --plugin-dir. To control which skill version runs, disable the global via
    --settings and point --plugin-dir at the version under test.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = Path(os.environ.get("PLUGIN_DIR", REPO_ROOT / "plugins" / "sontek-skills"))
PLUGIN_ID = "sontek-skills@sontek-skills-local"
# Flag precedence (> user/project) lets us force the globally-installed copy off.
_DISABLE_GLOBAL = json.dumps({"enabledPlugins": {PLUGIN_ID: False}})


@dataclass
class Transcript:
    """Parsed stream-json events from one `claude -p` run."""

    events: list[dict] = field(default_factory=list)
    path: Path | None = None

    @classmethod
    def parse(cls, path: Path) -> "Transcript":
        events: list[dict] = []
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # tolerate partial/garbage lines
        return cls(events, path)

    def _assistant_blocks(self):
        for e in self.events:
            if e.get("type") == "assistant":
                for b in e.get("message", {}).get("content", []) or []:
                    yield b

    @property
    def text(self) -> str:
        """Assistant prose + tool calls (name + input) + final result, one per line."""
        parts: list[str] = []
        for b in self._assistant_blocks():
            if b.get("type") == "text":
                parts.append(b.get("text", ""))
            elif b.get("type") == "tool_use":
                parts.append(f"{b.get('name', '')} {json.dumps(b.get('input', {}))}")
        for e in self.events:
            if e.get("type") == "result":
                parts.append(str(e.get("result") or ""))
        return "\n".join(parts)

    @property
    def tools_used(self) -> list[str]:
        return [b.get("name") for b in self._assistant_blocks() if b.get("type") == "tool_use"]

    @property
    def skills_fired(self) -> list[str]:
        out: list[str] = []
        for b in self._assistant_blocks():
            if b.get("type") == "tool_use" and b.get("name") == "Skill":
                inp = b.get("input", {}) or {}
                out.append(inp.get("skill") or inp.get("command") or "?")
        return out

    def skill_fired(self, name: str) -> bool:
        return any(s == name or s.endswith(f":{name}") for s in self.skills_fired)

    @property
    def available_skills(self) -> list[str]:
        for e in self.events:
            if e.get("type") == "system" and e.get("subtype") == "init":
                return e.get("skills", []) or []
        return []


def run_claude(
    prompt: str,
    cwd: Path,
    *,
    max_turns: int = 5,
    plugin: Path | None = PLUGIN_DIR,
    disable_global: bool = False,
    out_dir: Path | None = None,
    timeout: int = 300,
) -> Transcript:
    """Run one headless `claude -p` and return the parsed transcript.

    plugin: a dir to --plugin-dir (load that version live), or None to load none.
    disable_global: force the globally-installed cached plugin off via --settings.
    """
    cwd.mkdir(parents=True, exist_ok=True)
    out_dir = out_dir or Path(tempfile.mkdtemp(prefix="behav-out-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    tpath = out_dir / "transcript.jsonl"

    cmd = [
        "claude", "-p", prompt,
        "--dangerously-skip-permissions",
        "--max-turns", str(max_turns),
        "--output-format", "stream-json", "--verbose",
    ]
    if plugin is not None:
        cmd += ["--plugin-dir", str(plugin)]
    if disable_global:
        cmd += ["--settings", _DISABLE_GLOBAL]

    with open(tpath, "wb") as out, open(out_dir / "stderr.log", "wb") as err:
        try:
            subprocess.run(cmd, cwd=str(cwd), stdout=out, stderr=err, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            pass  # partial transcript is still worth parsing
    return Transcript.parse(tpath)


def edited_plugin(edits: dict[str, str], workdir: Path) -> Path:
    """Copy the plugin and append candidate text to named skill files.

    edits maps a path relative to the plugin root (e.g. "skills/clarify/SKILL.md")
    to text appended at end of file. Returns the copy's path for --plugin-dir.
    Used by edit-gating tests: the "after" arm points here, "before" at PLUGIN_DIR.
    """
    import shutil

    dst = workdir / "plugin"
    shutil.copytree(PLUGIN_DIR, dst)
    for rel, addition in edits.items():
        f = dst / rel
        f.write_text(f.read_text() + "\n" + addition + "\n")
    return dst

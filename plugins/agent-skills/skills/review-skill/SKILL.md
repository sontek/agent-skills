---
name: review-skill
description: Audit existing skills (SKILL.md files) against the write-skill authoring rubric — frontmatter validity, description trigger coverage, structural size, reference resolution, intra-skill cross-references. Use when reviewing a newly written skill, checking skill quality before merge, evaluating refactored or consolidated skills, or running a compliance pass over the skill plugin. Outputs findings classified as real gaps, observations, or pre-existing issues, each with a concrete recommended fix.
---

# Review Skill

Audit existing skills for compliance with the authoring standards in `write-skill`. Same rubric, applied as a checklist after-the-fact instead of as a guide during creation.

## Modes

Pick one before starting. Default to `branch` if not specified.

- **`branch`** — Review skills modified in the current branch's diff vs. main. Find changed skills via `git diff main...HEAD --name-only | grep -E '/skills/[^/]+/(SKILL\.md|references/|scripts/)'`.
- **`paths`** — Review an explicit list of skill directories provided by the invoker.

For each skill, the unit of review is the whole skill directory (SKILL.md + `references/` + `scripts/`), not just the SKILL.md file.

## Severity classification

Classify every finding into one of three tiers:

- **Real gap** — violates a hard requirement; would degrade auto-loading or break references. Fix before merge.
- **Observation** — soft guidance not met; worth flagging, decide whether to fix or defer.
- **Pre-existing** — issue was there before the change being reviewed. Note separately so it isn't blamed on the diff.

The pre-existing tier matters: when reviewing a single change, don't punish the author for issues they didn't introduce. Surface them so the team can address them later.

## Rubric

### Frontmatter

- `name` is kebab-case, 1-64 chars, matches the directory name.
- `description` is ≤ 1024 chars, written in third person.
- First sentence: what the skill does.
- Includes "Use when…" with concrete trigger keywords.
- Optional fields valid (`model` ∈ {sonnet, opus, haiku}; `allowed-tools` space-delimited; `license` is name or path).
- YAML is valid (no tabs, balanced quotes).

### Trigger discrimination — most important check

Synthesize 3-5 user phrasings that SHOULD trigger this skill and 3-5 that should NOT (similar-sounding but distinct, e.g. "review the plan" vs. "review the code").

For each SHOULD phrase, check whether the description has a keyword the agent would match on. If a SHOULD phrase has no matching keyword, that's a **real gap** — extend the description's "Use when…" clause.

Most skill drift comes from descriptions failing to cover their actual scope after refactors. Catching this is the primary value of this skill.

### Structure

- SKILL.md ≤ ~100 lines, OR remaining content is core to the workflow (modes, process, output format).
- Bulky reference content (pattern catalogs, exhaustive checklists, command references) lives in `references/*.md`.
- Concrete examples present.
- No time-sensitive info (dates, current versions of dependencies).
- Consistent terminology throughout.

### References resolve

- Every `references/*.md` link in SKILL.md resolves to an existing file.
- Every `scripts/*.py` invocation points to a script that exists in `scripts/`.
- Every other skill mentioned by name (e.g., "hand off to the `commit` skill") exists at `plugins/agent-skills/skills/<name>/`.
- References are one level deep (don't nest `references/sub/`).

### Skill vs. agent

- Skill is at `plugins/agent-skills/skills/<name>/SKILL.md`; agent is at `plugins/agent-skills/agents/<name>.md`.
- Naming matches type: skills are `verb-object`, agents are `role-noun`.
- Frontmatter matches type (agents use `model` + `tools`; skills use `allowed-tools` if any).

## Reporting

For each reviewed skill, output:

```markdown
## <skill-name>

**Verdict:** clean | needs attention

### Real gaps
- **[check name]** — Why it's a problem. Recommended fix: [concrete change].

### Observations
- **[check name]** — What to flag. Recommended action: [fix or defer].

### Pre-existing (not from this change)
- **[check name]** — Note for later, not blocking.

### Trigger test
- SHOULD trigger: [list]
- SHOULD NOT trigger: [list]
- Discrimination: pass | fail
```

If reviewing multiple skills, emit a one-line summary table at the top, then per-skill sections.

## What NOT to flag

- Stylistic preferences (heading style, list formatting) — focus on rubric compliance.
- Inline content that looks "splittable" but is core to the workflow.
- Trigger phrasings the model handles via synonyms naturally — only flag missing triggers when the gap would actually degrade auto-loading.
- Pre-existing issues outside the changed scope, unless asked for a full audit.

## Output discipline

- Real gaps first, observations second, pre-existing last.
- One paragraph per finding maximum.
- Always include a concrete recommended fix — "the description should say X" beats "the description is too narrow."
- Match `review-code`'s matter-of-fact tone — helpful, not accusatory.

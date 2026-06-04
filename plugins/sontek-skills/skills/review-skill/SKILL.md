---
name: review-skill
description: Audit existing skills (SKILL.md files) against the write-skill authoring rubric — frontmatter validity, description trigger coverage, structural size, reference resolution, intra-skill cross-references. Use when reviewing a newly written skill, checking skill quality before merge, evaluating refactored or consolidated skills, or running a compliance pass over the skill plugin. Outputs findings classified as real gaps, observations, or pre-existing issues, each with a concrete recommended fix.
---

# Review Skill

Route a skill audit through the `skill-reviewer` agent in isolated context. The skill resolves which skill directories are in scope; the agent applies the write-skill rubric and reports findings.

## When to invoke

- "Review this skill", "audit this SKILL.md", "check skill quality before merge"
- Compliance pass after a skill refactor or consolidation
- Run after `write-skill` ships a new skill, before opening the PR

Don't use for:

- Reviewing code, not skills — use `review-code`
- Authoring a new skill from scratch — use `write-skill`

## Modes

Pick one before invoking. Default to `branch` if unspecified.

- **`branch` (default)** — Review skills modified in the current branch's diff vs. main. Find changed skill directories via `git diff main...HEAD --name-only | grep -E '/(skills|agents)/[^/]+/' | awk -F/ '{print $1"/"$2"/"$3"/"$4}' | sort -u`.
- **`paths`** — Review an explicit list of skill or agent directories/files provided by the caller.

## Process

### 1. Resolve scope

- **`branch` mode:** compute the changed skill/agent directories from the diff (command above). For each directory, the agent will read SKILL.md + `references/` + `scripts/` (or the agent file directly).
- **`paths` mode:** take the explicit directory or file list from the caller.

### 2. Ground the review

Light pass for context-forwarding only. Do NOT apply the rubric yourself.

- Note whether each item in scope is a skill (`plugins/sontek-skills/skills/<name>/SKILL.md`) or an agent (`plugins/sontek-skills/agents/<name>.md`) — the agent uses different sub-rubrics for each.
- Capture any caller-supplied "this skill is intentionally large, the inline content is core workflow" notes — these flip what would otherwise be observations into known-accepted state.

### 3. Delegate to the skill-reviewer agent

Invoke via the Task tool with `subagent_type: sontek-skills:skill-reviewer`. Include in the prompt:

- The **mode** (`branch` or `paths`).
- The list of skill/agent paths in scope.
- Per-item caller notes — verbatim.

Example prompt skeleton:

```
Run a skill audit in `branch` mode.

In scope:
- plugins/sontek-skills/skills/review-code/ (skill)
- plugins/sontek-skills/skills/review-security/ (skill)
- plugins/sontek-skills/agents/code-reviewer.md (agent — new in this branch)

Caller notes:
- review-code/SKILL.md was just slimmed to a coordinator — large size is now expected
  to be ~60-90 lines, not the prior ~250.

Follow your rubric: frontmatter, trigger discrimination (most important),
structure, references resolve, skill-vs-agent typing. Classify findings as
real gap / observation / pre-existing.
```

### 4. Return the agent's output

Pass the agent's findings back to the caller verbatim. Don't summarize, re-prioritize, or filter.

For follow-up ("expand finding #2", "propose the description rewrite"), invoke the agent again with the relevant context.

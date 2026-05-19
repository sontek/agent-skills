# Agent Skills

Agent skills and subagents, following the [Agent Skills](https://agentskills.io) open format.

## Installation

### Claude Code from local clone

```bash
# Clone the repository
git clone git@github.com:sontek/agent-skills.git ~/agent-skills
```

Then **inside Claude Code**, run these slash commands:

```
/plugin marketplace add ~/agent-skills
/plugin install agent-skills@agent-skills-local
```

After installation, restart Claude Code. Skills and agents are automatically invoked when relevant to your task.

### Quick Test (No Installation)

```bash
# Run Claude Code with the plugin directory directly
claude --plugin-dir ~/agent-skills/plugins/agent-skills
```

### Updating

Inside Claude Code, run:

```
/plugin update agent-skills@agent-skills-local
```

Or use `/plugin` to open the interactive plugin manager.

## What's in this plugin

This plugin ships two kinds of capabilities:

- **Skills** — atomic workflows the main agent loads inline. `verb-object` naming (`create-pr`, `review-code`, `write-skill`).
- **Agents** — persona subagents that run in isolated context and compose skills with judgment. `role-noun` naming (`senior-engineer`, `security-auditor`).

See [Skills vs agents](#skills-vs-agents) for the decision guide.

## Available Skills

### Git workflow

| Skill | Description |
| --- | --- |
| [create-branch](plugins/agent-skills/skills/create-branch/SKILL.md) | Create git branches following `<type>/<description>` conventions |
| [commit](plugins/agent-skills/skills/commit/SKILL.md) | Conventional commits with strict AI attribution rules (only `Co-Authored-By`) |
| [create-pr](plugins/agent-skills/skills/create-pr/SKILL.md) | Create PRs; respects repo `PULL_REQUEST_TEMPLATE.md` when present |
| [iterate-pr](plugins/agent-skills/skills/iterate-pr/SKILL.md) | Iterate on a PR until CI passes and review feedback is addressed |
| [update-changelog](plugins/agent-skills/skills/update-changelog/SKILL.md) | Add notable user-facing changes since the last tag to `CHANGELOG.md`'s `## Unreleased` section |

### Code review & audit

| Skill | Description |
| --- | --- |
| [review-code](plugins/agent-skills/skills/review-code/SKILL.md) | Prioritized code review (P0-P3) with fail-fast error-handling rubric; `branch` mode (diff vs. main) or `paths` mode (explicit file list) |
| [auto-review-code](plugins/agent-skills/skills/auto-review-code/SKILL.md) | Loop `review-code` and `simplify` until no safe fixes remain; batches risky changes for a single end-of-run approval pass |
| [review-security](plugins/agent-skills/skills/review-security/SKILL.md) | OWASP-aligned security review with confidence-based reporting |
| [review-django-access](plugins/agent-skills/skills/review-django-access/SKILL.md) | Django/DRF IDOR and access-control review |
| [review-django-perf](plugins/agent-skills/skills/review-django-perf/SKILL.md) | Django performance review (N+1, unbounded queries, missing indexes) |
| [review-gha-security](plugins/agent-skills/skills/review-gha-security/SKILL.md) | GitHub Actions security review (pwn requests, expression injection, credential theft) |

### Planning & design

| Skill | Description |
| --- | --- |
| [grill-me](plugins/agent-skills/skills/grill-me/SKILL.md) | Interview the user one question at a time to stress-test a plan |
| [plan-implementation](plugins/agent-skills/skills/plan-implementation/SKILL.md) | Structured plan for NEW features (writes `IMPLEMENTATION_PLAN_*.md`) |
| [plan-refactor](plugins/agent-skills/skills/plan-refactor/SKILL.md) | Tiny-commit refactor plan (writes `REFACTOR_PLAN_*.md`) |
| [review-plan](plugins/agent-skills/skills/review-plan/SKILL.md) | Route an existing plan (file or plan-mode draft) through `senior-engineer` and `product-manager` for a judgment pass |
| [auto-review-plan](plugins/agent-skills/skills/auto-review-plan/SKILL.md) | Loop `review-plan` and auto-apply small blocking edits until the plan is clean; flags structural recommendations for end-of-run approval |
| [improve-architecture](plugins/agent-skills/skills/improve-architecture/SKILL.md) | Find architectural friction and design module-deepening refactors |
| [frontend-design](plugins/agent-skills/skills/frontend-design/SKILL.md) | Design distinctive frontend UIs with strong aesthetic direction (greenfield/redesign work) |

### Diagrams

| Skill | Description |
| --- | --- |
| [draw-mermaid-diagram](plugins/agent-skills/skills/draw-mermaid-diagram/SKILL.md) | Create and validate Mermaid diagrams of any type (flowchart, sequence, class, ER, state, gantt). Houses `tools/validate.sh` |
| [draw-infra-diagram](plugins/agent-skills/skills/draw-infra-diagram/SKILL.md) | AWS / cloud architecture specialist on top of `draw-mermaid-diagram` — adds shape vocabulary, color palette, region tinting, debugging-oriented composition |

### Session management

| Skill | Description |
| --- | --- |
| [handoff](plugins/agent-skills/skills/handoff/SKILL.md) | Write a structured `HANDOFF_<slug>.md` so a fresh session can continue the current work without re-reading the transcript. Use before `/clear` or when starting a new window mid-task |

### Tools & integrations

| Skill | Description |
| --- | --- |
| [librarian](plugins/agent-skills/skills/librarian/SKILL.md) | Cache remote git repos at `~/.cache/checkouts/<host>/<org>/<repo>` for stable, throttled-refresh local access |
| [sentry](plugins/agent-skills/skills/sentry/SKILL.md) | Fetch Sentry issues / events / transactions / logs via the Sentry API for debugging |
| [uv](plugins/agent-skills/skills/uv/SKILL.md) | Use `uv` for Python in repos that have adopted it — `uv run`, `uv add`, inline script metadata, `uv_build` |

### Meta

| Skill | Description |
| --- | --- |
| [write-skill](plugins/agent-skills/skills/write-skill/SKILL.md) | Create new skills and agents with proper structure and triggers |
| [review-skill](plugins/agent-skills/skills/review-skill/SKILL.md) | Audit existing skills against the `write-skill` rubric (frontmatter, trigger coverage, structure, references) |
| [write-agents-md](plugins/agent-skills/skills/write-agents-md/SKILL.md) | Write concise, high-signal `AGENTS.md` / `CLAUDE.md` files |

## Available Agents

Agents are persona subagents that run autonomously in isolated context. They use the skills above but bring experience and opinion.

| Agent | Description |
| --- | --- |
| [code-simplifier](plugins/agent-skills/agents/code-simplifier.md) | Autonomous refactoring specialist — refines recently modified code for clarity (opus) |
| [senior-engineer](plugins/agent-skills/agents/senior-engineer.md) | 15+ year SaaS engineer — opinionated architecture, scalability, maintainability (opus) |
| [security-auditor](plugins/agent-skills/agents/security-auditor.md) | Offensive + defensive security engineer — HIGH-confidence findings with PoC (opus) |
| [product-manager](plugins/agent-skills/agents/product-manager.md) | 15+ year PM with UX sensibility — user journeys, scope discipline, prioritization (opus) |
| [researcher](plugins/agent-skills/agents/researcher.md) | Web research specialist — source-cited findings with explicit confidence and conflicting-source flags (opus) |

See [agents/README.md](plugins/agent-skills/agents/README.md) for invocation triggers and when to use each one.

## Skills vs agents

| | Skills | Agents |
| --- | --- | --- |
| What | Atomic capabilities loaded inline | Personas/roles running in isolated context |
| Naming | `verb-object` (`create-pr`, `review-code`) | `role-noun` (`senior-engineer`, `code-simplifier`) |
| Location | `plugins/agent-skills/skills/<name>/SKILL.md` | `plugins/agent-skills/agents/<name>.md` |
| Frontmatter | `allowed-tools:` | `model:` (opus/sonnet/haiku) |
| Context | Runs in main conversation — user sees every step | Runs in isolated context — returns a final report |
| Best for | Conversational workflows | Fire-and-forget audits, persona judgment |

Use the [write-skill](plugins/agent-skills/skills/write-skill/SKILL.md) skill to create either one.

## Creating new skills

Skills follow the [Agent Skills specification](https://agentskills.io/specification). Each skill requires a `SKILL.md` file with YAML frontmatter.

### Skill template

Create a new directory under `plugins/agent-skills/skills/`:

```
plugins/agent-skills/skills/my-skill/
└── SKILL.md
```

**SKILL.md format:**

```yaml
---
name: my-skill
description: A clear description of what this skill does. Use when [specific triggers]. Include keywords that help the agent identify when this skill is relevant.
---

# My Skill Name

## Quick start

[Minimal working example]

## Workflow

[Step-by-step guidance]

## Examples

Concrete examples showing expected input/output.
```

### Naming conventions

- **name**: 1-64 characters, lowercase alphanumeric with hyphens only. `verb-object` for skills (e.g. `create-pr`), `role-noun` for agents (e.g. `code-simplifier`).
- **description**: Up to 1024 characters, include trigger keywords and "Use when..." clause.
- Keep `SKILL.md` under ~100 lines; split longer content into `references/*.md`.

Wrap prose at 80 chars if desired:

```bash
npx prettier --write --prose-wrap always --print-width 80 your-file.md
```

### Optional frontmatter fields

| Field | Description |
| --- | --- |
| `license` | License name or path to license file |
| `compatibility` | Environment requirements (max 500 chars) |
| `model` | Override model for this skill (e.g., `sonnet`, `opus`, `haiku`) |
| `allowed-tools` | Space-delimited list of tools the skill can use |
| `metadata` | Arbitrary key-value pairs for additional properties |

```yaml
---
name: my-skill
description: What this skill does
license: Apache-2.0
model: sonnet
allowed-tools: Read Grep Glob
---
```

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [getsentry/sentry-skills](https://github.com/getsentry/sentry-skills) — upstream we fork from
- [mattpocock/agent-skills](https://github.com/mattpocock/agent-skills) — source of `grill-me`, `improve-architecture`, `plan-refactor`
- [mitsuhiko/agent-stuff](https://github.com/mitsuhiko/agent-stuff) — source of `librarian`, `update-changelog`, `sentry`, `uv`, `frontend-design`, and the Mermaid validation tool used by `draw-mermaid-diagram` / `draw-infra-diagram`

## License

MPL-2.0

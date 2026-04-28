---
name: write-skill
description: Create new agent skills with proper structure, progressive disclosure, and bundled resources. Use when user wants to create, write, or build a new skill. Also covers when to ship a capability as an agent instead of a skill.
---

# Write Skill

A meta-skill for authoring new skills in this plugin.

To audit an existing skill against this rubric (after refactors, before merge, on consolidation), use the `review-skill` skill instead — it applies these checks to a skill that already exists.

## Before you start: skill or agent?

Decide early whether the capability should ship as a **skill** (SKILL.md in `skills/<name>/`) or an **agent** (single `.md` in `agents/`).

| Ship as a **skill** when... | Ship as an **agent** when... |
|---|---|
| The workflow is conversational/iterative | The task is fire-and-forget (audit, review, refactor) |
| The user invokes it inline | The task benefits from isolated context |
| Main conversation context matters (current git state, recent files) | You want a role/persona that brings judgment |
| Output is a back-and-forth with the user | You need a specific model (e.g. `opus` for deep reasoning) |
| Examples: `create-pr`, `commit`, `iterate-pr`, `grill-me` | Examples: `code-simplifier`, `senior-engineer`, `security-auditor` |

**Naming convention:**

- Skills: `verb-object` (e.g. `create-pr`, `review-code`, `write-skill`)
- Agents: `role-noun` (e.g. `code-simplifier`, `security-auditor`)
- Topic-review form acceptable for audit skills: `review-code`, `review-security`, `review-django-perf`

## Skill classification

Identify which type of skill you're creating. This drives structure:

| Class | Purpose | Example |
|-------|---------|---------|
| `workflow-process` | Multi-step process with clear phases | `create-pr`, `iterate-pr` |
| `integration-documentation` | Document an external/integration pattern | `write-agents-md` |
| `security-review` | Audit/review checklist | `review-security`, `review-gha-security` |
| `skill-authoring` | Meta (like this one) | `write-skill` |
| `generic` | None of the above | `grill-me` |

## Process

### 1. Gather requirements

Ask the user about:

- What task/domain does the skill cover?
- What specific use cases should it handle?
- Does it need executable scripts or just instructions?
- Any reference materials to include?
- Should this be a skill or an agent (see decision table above)?

### 2. Draft the skill

Create:

- `SKILL.md` with concise instructions
- Additional reference files if content exceeds 100 lines
- Utility scripts if deterministic operations are needed

### 3. Write description trigger tests

Before finalizing, write out:

- **3-5 queries that SHOULD trigger this skill** — e.g., "review this PR", "create a branch"
- **3-5 queries that should NOT trigger this skill** — edge cases that look similar but aren't

Verify the description discriminates between them. Adjust trigger keywords until the description handles both lists correctly.

### 4. Review with user

Present the draft and ask:

- Does this cover your use cases?
- Anything missing or unclear?
- Should any section be more or less detailed?

### 5. Lightweight evaluation

Run a qualitative check: pick one representative task this skill should handle, invoke it, and verify the output is what you'd expect. Fix obvious issues before shipping.

Skip formal eval metrics unless the skill is high-risk (security, production ops).

### 6. Register and validate

Before committing:

- Verify the skill is at `plugins/agent-skills/skills/<name>/SKILL.md` (or `plugins/agent-skills/agents/<name>.md` for an agent)
- Verify `description` is under 1024 characters
- Grep for intra-skill references: `rg '<other-skill-name>' plugins/agent-skills/skills/<name>/SKILL.md` — make sure anything referenced actually exists
- Verify frontmatter is valid YAML

## Skill structure

```
skills/<skill-name>/
├── SKILL.md           # Main instructions (required)
├── REFERENCE.md       # Detailed docs (if SKILL.md exceeds ~100 lines)
├── references/        # Multiple reference files by topic (if many)
│   └── topic.md
└── scripts/           # Utility scripts (if deterministic operations)
    └── helper.py
```

## SKILL.md template

```md
---
name: skill-name
description: Brief description of capability. Use when [specific triggers].
---

# Skill Name

## Quick start

[Minimal working example]

## Workflows

[Step-by-step processes with checklists for complex tasks]

## Advanced features

[Link to separate files: See [REFERENCE.md](REFERENCE.md)]
```

## Description requirements

The description is **the only thing your agent sees** when deciding which skill to load. It's surfaced in the system prompt alongside all other installed skills. Your agent reads these descriptions and picks the relevant skill based on the user's request.

**Goal:** give the agent just enough info to know:

1. What capability this skill provides
2. When/why to trigger it (specific keywords, contexts, file types)

**Format:**

- Max 1024 chars
- Write in third person
- First sentence: what it does
- Second sentence: "Use when [specific triggers]"

**Good example:**

```
Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when user mentions PDFs, forms, or document extraction.
```

**Bad example:**

```
Helps with documents.
```

The bad example gives your agent no way to distinguish this from other document skills.

## When to add scripts

Add utility scripts when:

- Operation is deterministic (validation, formatting, parsing)
- Same code would be generated repeatedly
- Errors need explicit handling
- Output is structured data the model would otherwise parse from text

Scripts save tokens and improve reliability vs generated code. Use `uv` for Python script management when the scripts need dependencies.

## When to split files

Split into separate files when:

- SKILL.md exceeds ~100 lines
- Content has distinct domains (e.g., separate auth/injection/xss references)
- Advanced features are rarely needed (progressive disclosure)

## Agent frontmatter (if shipping as an agent)

```md
---
name: role-noun-name
description: What this agent does. Auto-invokable when user says [triggers].
model: opus
tools: ["Read", "Grep", "Glob", "Bash", "Task"]
---

You are [persona description]. [Responsibilities, approach, constraints].
```

Key differences from skills:

- No `SKILL.md` filename — just `<name>.md` directly in `agents/`
- Specify `model` explicitly (opus for heavy reasoning, sonnet for standard work)
- Specify `tools` as an allowlist
- Body is the agent's system prompt, not a workflow document

## Output format (what you report back)

When you finish writing/updating a skill, report:

1. **Summary** — what the skill does in one sentence
2. **Changes Made** — files created/modified
3. **Validation Results** — did description trigger tests pass, does the lightweight eval look right
4. **Open Gaps** — anything the user should know that isn't covered

## Review checklist

Before handing off:

- [ ] Description includes explicit triggers ("Use when...")
- [ ] Description under 1024 chars
- [ ] SKILL.md under 100 lines (or justified split into references)
- [ ] No time-sensitive info
- [ ] Consistent terminology throughout
- [ ] Concrete examples included
- [ ] References are one level deep (don't nest)
- [ ] Intra-skill references point to skills that actually exist
- [ ] Frontmatter is valid YAML
- [ ] Skill vs agent decision is documented (in the description or a comment)

---
name: document-architecture
description: Generate a high-level architecture document for a module, service, or codebase using 4 parallel Explore sub-agents (data, API/interface, business logic, integrations). Composes with `draw-mermaid-diagram` and `draw-infra-diagram` to embed validated diagrams. Use when asked to "document this codebase", "write architecture docs", "create an arch doc", "generate onboarding docs", "document this service", "map this module". Output is a single Markdown file optimized for human onboarding, not LLM context.
---

# Document Architecture

Fan out 4 parallel Explore sub-agents to gather raw findings on Data, API/Interface, Business Logic, and Integrations; synthesize into one human-readable Markdown architecture document; embed validated Mermaid diagrams. Goal: a future engineer can read this file and understand what the system does and how it fits together.

This is **not**:

- A find-and-fix tool — use `improve-architecture` to surface refactor opportunities.
- An AGENTS.md / CLAUDE.md generator — use `write-agents-md` for terse agent-facing docs (~60 lines).
- A repo-map / symbol index — there's no symbol-level output; the output is prose with file:line references.

`improve-architecture` finds friction *to fix*; this skill produces the *current-state* map. They are complements.

## When to invoke

- "Document this codebase", "write architecture docs", "create an arch doc"
- "Generate onboarding docs for new engineers"
- "Document this service" / "map this module"
- Pre-handoff documentation when an engineer is rotating off a project

Don't use for:

- A refactor proposal — use `improve-architecture`
- Agent-facing instructions — use `write-agents-md`
- API reference docs — those belong with the code (OpenAPI / docstrings)

## Process

### 1. Resolve scope

Determine what to document. In order of preference:

- An explicit path the caller provided (`app/payments/`, `services/auth/`)
- A clearly-named module in the repo if the caller named it ("document the orders service")
- Whole repo if the caller said so explicitly — but confirm first; this is expensive and often produces a doc too broad to be useful

Determine the output path. Default: `docs/architecture/<scope-slug>.md`. If `docs/` doesn't exist, ask before creating it. If the caller passed `--save path/to/file.md`, use that.

### 2. Read the template

Read [REFERENCE.md](REFERENCE.md) for the section structure and reference-format rules. Every agent prompt and the final synthesis follow that template.

### 3. Launch 4 parallel Explore sub-agents

In a **single message with 4 Task calls**, invoke `subagent_type: Explore` (or `general-purpose` if Explore isn't available — Explore is read-only-search-shaped and ideal here). Each agent gets a self-contained prompt covering only its layer. They run concurrently.

Each agent's prompt includes:

- The scope (explicit path list).
- Their assigned layer (Data / API / Logic / Integrations) and what to search for (see [REFERENCE.md](REFERENCE.md) §"Sub-agent layer briefs").
- Output discipline: **raw findings only** (bullet points, lists, file:line refs). **No prose narrative**, **no code snippets**, **no implementation details**. Speed matters; the main agent composes the final doc.
- Search exclusions: skip `tests/`, `test_*.py`, `*_test.go`, `migrations/`, `node_modules/`, `dist/`, `build/`, `vendor/`.
- Diagram candidates: list 1–2 diagrams that would best convey this layer, with the type (`er`, `sequence`, `flowchart`, `state`, `class`) and a brief justification.

### 4. Synthesize

When all 4 agents return:

- Map their findings onto the template sections (see [REFERENCE.md](REFERENCE.md) §"Template structure"). Most findings have an obvious home; cross-cutting findings (e.g. an audit log used by every layer) go in their own subsection under Core Architecture.
- Identify the 3–5 most important data flows and write them step-by-step with file:line refs.
- Distill architectural decisions: name each one (e.g. "Async-first request handling", "Event-driven worker fanout") and state the trade-off in one or two sentences.
- Cap doc length at ~1000 lines. If you're heading past that, the scope was too broad — call it out in the summary section and ship the doc you have.

### 5. Pick and draft diagrams

From the candidates each agent suggested, pick **3–5 total** (any more dilutes attention). Bias toward:

- One **system overview flowchart** showing the top-level components (always include).
- One **ER diagram** for the data layer if there's a real schema.
- One **sequence diagram** for the most important workflow.
- Optional: a **state diagram** for a clear lifecycle, or a **class diagram** for an OO-heavy module.

For each chosen diagram, route through the appropriate skill:

- AWS / cloud-infra-shaped → `draw-infra-diagram`
- Everything else → `draw-mermaid-diagram`

Draft each diagram as a standalone `.mmd` file under `docs/architecture/diagrams/` (or alongside the doc if `docs/` doesn't exist). Validate with the bundled validator:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/draw-mermaid-diagram/tools/validate.sh diagram.mmd
```

A diagram that fails validation gets re-drafted, not skipped silently — a broken diagram in the doc is worse than no diagram.

### 6. Write the doc

Inline each validated diagram as a fenced ```mermaid block at its section. Keep the structure consistent across all sections (see [REFERENCE.md](REFERENCE.md) §"Template structure"). Use file:line references throughout — never inline code snippets except inside diagrams.

### 7. Report

After writing:

```
Documentation written: docs/architecture/<scope>.md (~<N> lines)

Diagrams (validated):
- docs/architecture/diagrams/<scope>-overview.mmd  (flowchart)
- docs/architecture/diagrams/<scope>-data.mmd      (ER)
- docs/architecture/diagrams/<scope>-checkout.mmd  (sequence)

Coverage:
- Data layer: <N> models / <N> stores
- API layer: <N> routes / <N> CLI commands
- Business logic: <N> services / <N> workflows
- Integrations: <N> external clients / <N> internal deps

Open gaps (not documented):
- <anything the agents couldn't find or that was out of scope>
```

## Output discipline

- **Single Markdown file** — not a directory of split files.
- **File:line references only** — never code snippets in prose. Diagrams are the only allowed "embedded code."
- **No emojis, no Unicode arrows** — keep it portable. Diagrams handle the visual layer.
- **Human-readable, not LLM-context-optimized** — write in complete sentences in sections that can be skimmed.

## Refresh policy

This doc captures a point in time. When the system changes materially, re-run this skill against the same scope; the agents re-discover and the doc gets overwritten. Diff the new vs old via `git diff` if you want a changelog. Don't try to maintain the doc by hand — drift is silent and the next reader trusts what they read.

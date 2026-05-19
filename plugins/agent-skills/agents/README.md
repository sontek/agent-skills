# Agents

This directory contains subagent definitions. Unlike skills (which are loaded as instructions into the main agent's context), agents run autonomously in isolated contexts and can be invoked automatically when their triggers match.

## Skills vs agents — when to use which

| | Skills | Agents |
|---|---|---|
| **What they are** | Atomic capabilities the main agent uses inline | Personas/roles that use skills with judgment and autonomy |
| **Naming** | `verb-object` (e.g. `create-pr`, `review-code`) | `role-noun` (e.g. `senior-engineer`, `code-simplifier`) |
| **Location** | `plugins/agent-skills/skills/<name>/SKILL.md` | `plugins/agent-skills/agents/<name>.md` |
| **Frontmatter** | `allowed-tools:` lists permitted tools | `model:` specifies runtime model |
| **Context** | Runs in main conversation — user sees every step | Runs in isolated context — returns a final report |
| **Invocation** | Inline, interactive, iterative | Fire-and-forget, can be auto-invoked via Task tool |
| **Best for** | Conversational workflows (`commit`, `iterate-pr`) | Audits, reviews, persona judgment (`security-auditor`) |

## Available agents

### code-simplifier

Autonomous refactoring specialist. Refines recently modified code for clarity and consistency while preserving functionality. Based on Anthropic's code-simplifier with added slop-scan detection rules for common AI-generated patterns (error swallowing, trivial async wrappers, placeholder comments, etc.).

**Auto-invokes when:** code has just been written/modified and would benefit from a clarity pass.

**Uses:** project `CLAUDE.md` / `AGENTS.md` standards if present.

### senior-engineer

15+ years building scalable SaaS platforms. Opinionated technical reviewer focused on scalability, maintainability, operational cost, testability, and architectural trade-offs. Also reviews plans (`IMPLEMENTATION_PLAN_*.md`, `REFACTOR_PLAN_*.md`, plan-mode drafts) for DRY, coupling, phase ordering, and missed seams.

**Auto-invokes when:** user says "review as a senior engineer", "architectural review", "will this scale", "put on your senior engineer hat", "review this plan", "analyze the plan", "critique the plan", etc.

**Uses:** `review-code`, `review-security`, `improve-architecture` skills for the mechanical pass; layers judgment on top. Invoked by the `review-plan` skill for plan reviews.

### security-auditor

Offensive + defensive security engineer. Thinks like an attacker, produces HIGH-confidence findings with full exploitation PoCs. Dedicated audit context — doesn't pollute main chat with security findings during regular work.

**Auto-invokes when:** user says "audit for security", "check vulnerabilities", "OWASP review", "security posture", etc.

**Uses:** `review-security`, `review-gha-security`, `review-django-access` skills.

### product-manager

15+ years shipping consumer and enterprise products. Strong UX sensibility. Cares about user journeys, scope discipline, information architecture, edge-case UX (error/empty/loading states), and feature prioritization frameworks (RICE, Kano, JTBD). Also reviews plans for user-facing work (scope creep, per-phase user impact, missing error/empty/loading-state plans).

**Auto-invokes when:** user says "review as a product manager", "PM review", "UX review", "is this the right feature", "prioritize these", etc. Invoked by the `review-plan` skill when the plan has user-facing surface.

### researcher

Web research specialist. Produces source-cited findings with explicit confidence levels and flags for conflicting or stale sources. Runs in isolated context so raw search results stay out of the caller's window. Doesn't make architectural decisions or write code — its output informs the caller's decision, it doesn't replace it.

**Auto-invokes when:** caller needs an external fact, library comparison, API behavior, RFC summary, "what's the current best practice for X" — anything that benefits from web search + synthesis with citations.

**Uses:** `WebSearch`, `WebFetch` for external sources; `Read`, `Grep`, `Glob`, `Bash` for local cross-referencing.

## Adding a new agent

1. Create `<role-noun-name>.md` in this directory
2. Include required frontmatter: `name`, `description`, `model`, optional `tools`
3. Write the body as the agent's system prompt — persona + approach + output format
4. Add an entry to this README
5. Use the `write-skill` skill (Section "Writing agents vs skills") for full authoring guidance

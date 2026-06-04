---
name: plan-implementation
description: Create structured implementation plans for NEW features, complex additions, or multi-phase work. Use when user asks to "create a plan" or "make an implementation plan" or work requires multiple distinct phases. Outputs a local IMPLEMENTATION_PLAN_<feature-name>.md file with reconnaissance findings, binary Ideal State Criteria, premortem, phases, and quality gates. For restructuring existing code without changing behavior, use plan-refactor instead. If Claude Code is in plan mode, plan mode itself already produces an in-conversation plan via ExitPlanMode — use review-plan on that draft instead of invoking this skill.
---

# Implementation Plan

Create structured implementation plans for complex features, refactoring,
or multi-phase work. Plans separate the *what* (intent, behavior, scope,
binary acceptance criteria) from the *how* (architecture, phases, tasks)
so each can be reviewed independently.

## When to create an implementation plan

Create a plan when:

- Feature requires multiple distinct phases or steps
- Refactoring affects multiple files or systems
- Work will span multiple commits or PRs
- Task requires coordination across different areas
- Breaking down complex work helps clarify approach
- Need to track progress on long-running work

**Don't create a plan for:**

- Simple bug fixes
- Single-file changes
- Trivial updates
- Well-understood, straightforward tasks

## Plan file

Plans live at the repo root as `IMPLEMENTATION_PLAN_<feature-name>.md`
in kebab-case.

**Examples:**

- `IMPLEMENTATION_PLAN_user-authentication.md`
- `IMPLEMENTATION_PLAN_async-queue-processing.md`
- `IMPLEMENTATION_PLAN_api-v2-migration.md`

## Plan structure

A plan has the following top-level sections, in this order:

1. **Overview** — 2–4 sentence summary of what's being built and why.
2. **Reconnaissance** — relevant files, conventions, dependencies,
   gotchas surfaced *before* designing. Prevents the plan from
   contradicting the codebase.
3. **Intent** — distilled what + why. What problem does this solve and
   for whom?
4. **Behavior** — happy path and edge cases the feature must handle.
5. **Scope** — explicit in-scope and out-of-scope lists.
6. **Effort and Quality** — pinned level, test depth, doc depth.
7. **Ideal State Criteria** — binary checkbox criteria including
   anti-criteria (things that must NOT happen).
8. **Phases** — ordered phases with tasks and quality gates.
9. **Premortem** — load-bearing assumptions and realistic failure
   modes.
10. **Notes** — decisions, open questions, dependencies.

## Creating the plan

### Phase 1: Reconnaissance (before designing)

Before writing any of the plan, gather concrete facts about the
codebase. Don't infer from filenames — read the files. For broader
sweeps, delegate to the `Explore` agent so the raw search output stays
out of your context.

Capture under the **Reconnaissance** section:

```markdown
## Reconnaissance

### Relevant Files
- `path/to/file.ext` — what it does and why it matters here

### Conventions
- <patterns adjacent code already uses — type aliases, error handling
  style, test layout, naming>

### Dependencies and Config
- <libraries, framework versions, config files relevant to this work>

### Key Findings
- <facts that directly shape the design>

### Gotchas
- <coupling, hidden invariants, missing tests, edge cases the design
  must respect>
```

Only include sections with substance. Drop the header if empty.

### Phase 2: Understand the requirements

- Read all requirements and context from the user
- Ask clarifying questions only if the answer changes the design
- If a question is a codebase fact, answer it from the reconnaissance
  instead of asking the user
- Identify dependencies and constraints

### Phase 3: Pin effort and Ideal State Criteria

Before designing phases, pin the effort dial and write binary
**Ideal State Criteria** (ISC). Each ISC is a yes/no checkable
condition — either it's met or it isn't, no "kind of."

```markdown
## Effort and Quality

- **Level:** Prototype / MVP / Production / Critical
- **Tests:** none / smoke / thorough / comprehensive
- **Docs:** none / inline / README / full

## Ideal State Criteria

### Core Functionality
- [ ] ISC-1: <atomic yes/no criterion>
- [ ] ISC-2: <atomic yes/no criterion>

### Edge Cases
- [ ] ISC-3: <atomic yes/no criterion>

### Anti-Criteria
- [ ] ISC-A-1: No <thing that must not happen>
```

**Good ISC** is concrete and measurable:

- ✅ `ISC-1: Login completes <500ms p95 on staging`
- ✅ `ISC-2: Failed login returns 401 without revealing whether the email exists`
- ✅ `ISC-A-1: No session cookies set without HttpOnly + Secure flags`

**Bad ISC** is subjective:

- ❌ `Login should be fast and user-friendly`
- ❌ `Handle errors gracefully`

The Anti-Criteria bucket is the one most plans skip — and most often
regret. Always include at least one.

### Phase 4: Break work into phases

Each phase should be:

- Independently committable
- Sequentially built on the previous one
- Small enough to complete in one session (1–3 hours)
- Tied back to specific ISC items

Use the phase template below.

### Phase 5: Premortem before writing the plan file

Before saving the file, write the premortem:

```markdown
## Premortem

### Load-bearing assumptions
- <assumption the plan relies on — and how we'd notice if it's wrong>

### Realistic failure modes
- <what could go wrong> — <mitigation OR accepted with reason>
```

Aim for 2–5 of each. Ask the user whether to mitigate or accept each
failure mode before committing the plan to disk.

### Phase 6: Write the plan file

Use the full template (next section) and write the file with the
`Write` tool. Then offer to run `review-plan` for a senior-engineer /
product-manager judgment pass — the cheapest point to catch
architectural mistakes is before any code is written.

## Phase template

Every phase has tasks and quality gates. Every task carries three
required fields so an implementer (you, a teammate, or a future
session) can execute without guessing.

```markdown
## Phase N: [Phase Name]

**Goal:** [Clear statement of what this phase achieves]
**Status:** Not Started | In Progress | Complete

### Tasks

- [ ] **<short task title>**
  - **Reference:** `path/to/existing/file.ext:line` or inline snippet
    showing the pattern to follow
  - **Constraints:** explicit rules and anti-patterns (e.g., "must use
    existing `JSONDict` alias", "no inline error swallowing")
  - **Acceptance:** verifiable check tied to ISC (e.g., "passes
    `pytest tests/auth/test_login.py::test_failed_login_no_email_leak`
    — satisfies ISC-2")

### Quality Gates

- [ ] Code review (self-review changes before moving to next phase)
- [ ] Tests passing (run test suite and verify all tests pass)
- [ ] Linter passing (run linter and fix all issues)
- [ ] Type checker passing (run type checker and fix all issues)
- [ ] Manual testing (verify functionality works as expected)
```

**Why every task needs the three fields:** without a concrete
reference, the implementer guesses at conventions. Without explicit
constraints, they reinvent local patterns. Without verifiable
acceptance, "done" stays subjective. If a task can't carry all three,
it's not ready to plan — split it further or scout more.

**Phase status values:**

- **Not Started** — Phase hasn't been started yet
- **In Progress** — Currently working on this phase
- **Complete** — All tasks and quality gates are finished

## Full plan template

```markdown
# Implementation Plan: [Feature Name]

**Created:** [Date]
**Status:** Not Started | In Progress | Complete

## Overview

[2–4 sentence summary of what's being built and why.]

## Reconnaissance

[See Phase 1 — Relevant Files, Conventions, Dependencies, Key
Findings, Gotchas. Omit subsections with no substance.]

## Intent

[Distilled what + why. What problem does this solve and for whom?]

## Behavior

### Happy Path
1. ...

### Edge Cases
- ...

## Scope

### In Scope
- ...

### Out of Scope
- ...

## Effort and Quality

- **Level:** ...
- **Tests:** ...
- **Docs:** ...

## Ideal State Criteria

### Core Functionality
- [ ] ISC-1: ...

### Edge Cases
- [ ] ISC-2: ...

### Anti-Criteria
- [ ] ISC-A-1: No ...

## Phases

### Phase 1: ...
[See phase template]

### Phase 2: ...
[See phase template]

## Premortem

### Load-bearing assumptions
- ...

### Realistic failure modes
- ... — Mitigation: ... | Accepted because: ...

## Notes

### Decisions Made
- [Key architectural or implementation decisions]

### Open Questions
- [ ] ...

### Dependencies
- [External dependencies or prerequisites]
```

## Working with the plan

### Starting a phase

1. Update phase status: `**Status:** In Progress`
2. Read through tasks and quality gates
3. Ensure previous phases are complete
4. Create feature branch if needed

### During implementation

- Check off tasks as completed
- Add notes about unexpected issues or decisions
- Keep the plan current with actual implementation

### Completing a phase

Before marking a phase complete:

1. Verify all tasks are checked off
2. Complete all quality gates:
   - [ ] Self-review code changes
   - [ ] Run tests: `pytest` or equivalent
   - [ ] Run linter: `ruff check .` or equivalent
   - [ ] Run type checker: `mypy .` or equivalent
   - [ ] Manually test the changes
3. Commit the phase changes
4. Mark phase as complete: `**Status:** Complete`
5. Commit the updated plan

### Updating the plan

The plan is a living document:

- Add phases if you discover additional work
- Adjust phases if the approach changes
- Add notes about important decisions or issues
- Update status regularly

## Tips for good plans

**Keep phases small:**

- Each phase should be completable in 1–3 hours
- If a phase is too large, break it into multiple phases
- Smaller phases are easier to review and commit

**Be specific in tasks:**

- "Add User model with email, password_hash, role fields" beats "Add
  User model"
- Specific tasks make the three required fields (reference,
  constraints, acceptance) easier to fill in

**Write binary ISC, not aspirations:**

- "ISC-1: `/auth/login` returns 200 with valid creds" — verifiable
- "ISC-1: Login should work" — subjective, useless

**Always write at least one anti-criterion:**

- "ISC-A-1: No raw passwords in logs" forces the design to consider
  failure modes the happy path hides

**Update as you go:**

- Add phases if you discover more work
- Mark tasks complete as you finish them
- Add notes about important decisions

**Use quality gates consistently:**

- Always include the standard quality gates
- Add project-specific gates if needed (e.g., "Security review")

**Commit plan updates:**

- Commit the plan with the code changes for each phase
- This creates a history of progress

## Tool usage

- **Write** — create initial `IMPLEMENTATION_PLAN_<feature>.md`
- **Edit** — update plan as work progresses
- **Read** — review current plan state
- **Bash** — run quality gate checks (tests, linter, type checker)
- **Task → Explore** — delegate broad reconnaissance sweeps to keep
  raw search output out of your context

## Integration with other skills

**Use with review-plan skill:**

- After writing the plan, offer `review-plan` for a senior-engineer /
  product-manager judgment pass before implementation starts.
- `review-plan` checks ISC presence, premortem coverage, and phase
  ordering — apply any blocking findings by editing the plan file,
  then begin Phase 1.

**Use with grill-me skill:**

- For especially fuzzy requirements, run `grill-me` before
  reconnaissance to nail down the user's intent.

**Use with commit skill:**

- Reference plan phases in commit messages:
  `feat(auth): Implement Phase 2 — Authentication service`
- Commit plan updates along with code changes

**Use with review-code skill:**

- Review each phase's changes before marking complete
- Quality gates include code review checkpoint

**Use with create-pr skill:**

- Create PRs per phase for large features, or one PR for smaller
  features. Reference the plan in the PR description.

## Common mistakes

**Don't use generic filenames:**

- ❌ `IMPLEMENTATION_PLAN.md` (conflicts with other plans)
- ✅ `IMPLEMENTATION_PLAN_user-authentication.md`

**Don't skip reconnaissance:**

- ❌ Planning architecture before reading the relevant files — the
  plan ends up contradicting existing conventions
- ✅ Read the files, surface conventions and gotchas, *then* design

**Don't write subjective ISC:**

- ❌ `ISC-1: Login should be secure`
- ✅ `ISC-1: Login rejects requests with malformed JWTs (400, no
  partial processing)`

**Don't skip the premortem:**

- ❌ Plan reads as if everything will work the first time
- ✅ 2–5 load-bearing assumptions called out so failure is auditable

**Don't make phases too large:**

- ❌ Phase 1: Implement entire authentication system
- ✅ Phase 1: Add database models for authentication

**Don't write vague tasks:**

- ❌ Task: "Fix the thing"
- ✅ Task with reference, constraints, and acceptance fields filled
  in

**Don't let plan get stale:**

- ❌ Plan says "In Progress" on Phase 2, actually on Phase 4
- ✅ Update plan status as you complete each phase

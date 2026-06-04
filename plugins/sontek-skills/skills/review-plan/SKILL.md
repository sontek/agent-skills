---
name: review-plan
description: Review a plan for architectural, DRY, scope, and UX concerns before implementation starts. Covers IMPLEMENTATION_PLAN_*.md / REFACTOR_PLAN_*.md files AND in-conversation plans drafted in Claude Code plan mode (ExitPlanMode) or inline messages. Use when user asks to "review the plan", "analyze the plan", "critique the plan", "is this plan good", or wants a senior engineer / product manager pass over a planning document. For creating a plan from scratch use plan-implementation or plan-refactor. For reviewing code or a PR use review-code.
---

# Review Plan

Stress-test a plan before implementation begins. Routes the plan through
the `senior-engineer` agent (architecture, DRY, scalability, phase
ordering) and, when the plan has user-facing surface, the
`product-manager` agent (scope, UX, prioritization). Returns a combined,
prioritized list of plan edits.

## When to invoke

- User has an `IMPLEMENTATION_PLAN_*.md` or `REFACTOR_PLAN_*.md` and wants
  a critique before starting work
- User is in Claude Code plan mode and wants the drafted plan reviewed
  before approving/exiting plan mode
- User drafted an ad-hoc plan inline in a message and wants a review pass
- User says "review the plan", "analyze the plan", "put your senior
  engineer hat on and review this plan"

Don't use for:

- Reviewing a PR or already-shipped code — use `review-code`
- Creating a plan from scratch — use `plan-implementation` or `plan-refactor`
- Interactive pre-plan clarification — use `grill-me`

## Process

### 1. Locate the plan

The plan lives in one of these places — check in order:

1. **Plan mode / inline conversation plan.** If the assistant just
   drafted a plan via `ExitPlanMode` or inline in a recent message,
   treat that text as the plan. No file to read.
2. **Plan file at repo root.** `IMPLEMENTATION_PLAN_<feature>.md` or
   `REFACTOR_PLAN_<feature>.md`.
3. **User-supplied path.** If the user pointed at a specific file, use
   that.

If multiple candidates exist and the user didn't name one, ask which.

### 2. Ground the review in real code

Before delegating to agents, read the key files the plan proposes to
touch or depends on. This prevents the agents from critiquing plan
assumptions that don't match the current codebase. Keep this pass
short — the agents do their own deeper exploration.

Note whether the plan has user-facing surface (UI, API contracts,
user-visible flows). This decides whether to run the PM pass.

### 2a. Check plan structure for missing load-bearing sections

Before delegating, scan the plan for these structural elements. Their
absence is itself a finding worth surfacing — hand-written or plan-mode
drafts often skip them:

- **Binary Ideal State Criteria (ISC)** — yes/no checkable conditions
  including at least one anti-criterion ("must NOT do X"). Subjective
  criteria like "should be fast" or "handle errors gracefully" don't
  count. If ISC are missing or all subjective, flag as a blocking
  concern.
- **Premortem** — load-bearing assumptions and realistic failure
  modes called out explicitly. A plan that reads as if everything
  will work the first time is hiding risk. If absent, flag.
- **Reconnaissance / current-state findings** — relevant files,
  conventions, and gotchas the plan respects. If the plan reasons in
  the abstract without grounding in the actual codebase, flag.
- **Per-task specificity** — each task should be implementable
  without guessing. If tasks are one-liners with no reference,
  constraints, or acceptance criteria, flag.

Surface these in the final report under a dedicated "Plan structure
gaps" subsection so the user can patch them before re-reviewing.

### 3. Delegate to senior-engineer

Use the Task tool with `subagent_type: sontek-skills:senior-engineer`.
Subagents have isolated context, so pass the plan explicitly:

- **File-based plan:** include the absolute path.
- **In-conversation plan:** inline the full plan text in the prompt.

Include a one-paragraph summary of the current-state code you observed
and explicit asks: DRY / duplication risk, coupling, leaky abstractions,
missing seams, scalability concerns, phase ordering, missing quality
gates, under-scoped testing, risky migrations.

Also ask it to evaluate plan structure: are ISC binary and
verifiable, do anti-criteria exist, is the premortem honest about
load-bearing assumptions, are per-task references / constraints /
acceptance criteria specific enough to implement without guessing.

Ask it to separate "resolve before starting" from "worth watching."

### 4. Delegate to product-manager (only if user-facing)

If the plan has user-facing surface, use the Task tool with
`subagent_type: sontek-skills:product-manager`. Pass the plan the same
way (path or inline text). Ask it to:

- Check each phase has clear user impact
- Flag scope creep or phases that can be cut/deferred
- Check error/empty/loading states are planned
- Challenge whether the solution matches the stated user problem

Skip this step for pure infra/refactor/internal-only plans.

### 5. Synthesize and report

Combine both reports. Deduplicate overlapping findings (both personas
often flag the same scope issue from different angles — merge them).

For plan-mode reviews, tell the user to either revise the drafted plan
before calling `ExitPlanMode` again, or exit plan mode and address the
findings during implementation.

## Output format

```markdown
## Plan Review: <plan filename or "plan mode draft">

**Verdict:** Ready to implement / Revise before starting / Rethink approach

### Plan structure gaps
Missing or weak load-bearing sections (binary ISC, anti-criteria,
premortem, reconnaissance, per-task specificity). Omit the heading if
none apply.

### Blocking concerns
Items to resolve before implementation starts. Each linked to the
specific phase/section it applies to.

### Worth considering
Softer concerns the user may choose to accept.

### Long-term watch-outs
Things that are fine now but will matter at scale or over time.

### Recommended plan edits
1-3 concrete changes to the plan before starting work.
```

## Integration with other skills

- Run after `plan-implementation` or `plan-refactor`, before
  implementation starts.
- Run on a plan-mode draft before calling `ExitPlanMode` — it's the
  cheapest point to catch architectural mistakes.
- Use `grill-me` *before* writing the plan for upfront clarification;
  use `review-plan` *after* writing it for a judgment pass.

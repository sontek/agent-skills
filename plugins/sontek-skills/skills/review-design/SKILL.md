---
name: review-design
description: Architectural / design review of EXISTING code at module scope — coupling, abstraction depth, seams, testability, scalability. Routes the code through the senior-engineer agent (and product-manager when it has user-facing surface) and returns a verdict plus prioritized concerns. Use when asked to "design review this module", "architectural review of this code", "is this module well-designed / too coupled", "review the design of X", "will this service scale", or "put your senior-engineer hat on" over a module or package. Distinct from review-code (diff-scoped bug/security/perf finders), review-plan (reviews a planning doc, not code), and improve-architecture (explores the whole codebase and proposes new designs as RFCs — generative, not evaluative).
allowed-tools: Read, Grep, Glob, Bash, Task
---

# Review Design

Evaluate the architecture of existing code at **module scope** and return a senior
engineer's verdict. This routes the module through the `senior-engineer` agent
(coupling, DRY, abstraction depth, missing seams, testability, scalability, phase
of evolution) and, when the module has user-facing surface, the `product-manager`
agent (is the design serving the right user problem). You get a prioritized
judgment, not a fix and not a diff review.

This is the code sibling of `review-plan`: same two judgment agents, same verdict
shape, but pointed at shipped code instead of a planning document.

## When to invoke

- "Design review this module / service / package", "architectural review of this code"
- "Is this module too coupled / too shallow / well-designed?", "will this scale?"
- "Review the design of `<path>`", "put your senior-engineer hat on over this code"
- Before a refactor, to get a judgment on what's actually wrong with the current shape

Don't use for:

- A diff / branch / PR for bugs, security, perf — use `review-code` (or `review-pr` for comments)
- A planning document (`IMPLEMENTATION_PLAN_*.md`, plan-mode draft) — use `review-plan`
- Exploring the whole codebase to *propose* new module designs as RFCs — use `improve-architecture` (generative; this skill is evaluative)
- Applying architectural changes — this is propose-only; hand the verdict to `plan-refactor`

## Process

### 1. Resolve scope

Take the module under review from the caller: a directory, a package, or an explicit
set of files that form one cohesive unit. Resolve it to a concrete file list
(`git ls-files <dir>` or the caller's list).

Do **not** default to the whole repository — a design review needs a bounded unit to
reason about. If the caller didn't name one, ask which module. If they named a broad
area, confirm the boundary before proceeding.

### 2. Ground the review in the code

Before delegating, read enough to brief the agents accurately — the module's public
interface, its main types/entry points, what it depends on, and who calls it (a quick
`grep` for importers). Keep this pass short; the agents do their own deeper
exploration. The point is to hand them an accurate map of the boundary, not to review
it yourself.

Note whether the module has **user-facing surface** (UI, API contracts, user-visible
flows). This decides whether to run the PM pass (step 4).

Capture any caller "this is intentional / out of scope" notes verbatim to forward.

### 3. Delegate to senior-engineer

Use the Task tool with `subagent_type: sontek-skills:senior-engineer`. Subagents have
isolated context, so the prompt is self-contained: include the resolved file list, the
one-paragraph map from step 2, the caller's notes verbatim, and explicit asks —

- Coupling and cohesion: is this module doing one thing, or several glued together?
- Abstraction depth: shallow modules (large interface, small benefit), leaky
  abstractions, pass-through layers that add no value.
- Missing seams: what can't be tested or replaced in isolation, and why.
- DRY / duplication against the rest of the codebase (it has Grep/Read — let it look).
- Scalability and the evolution path: what's fine now but bends at 10x.
- Error handling, observability, and backwards-compatibility posture of the interface.

Ask it to separate **"fix before building on this"** from **"worth watching."** Tell it
to follow its own output format.

### 4. Delegate to product-manager (only if user-facing)

If the module has user-facing surface, use the Task tool with
`subagent_type: sontek-skills:product-manager`, same self-contained prompt shape. Ask
it to challenge whether the design serves the stated user problem, whether
error/empty/loading paths exist, and whether complexity is buying real user value.
Skip entirely for pure infra / internal modules.

### 5. Synthesize and report

Combine the reports. Deduplicate overlapping findings (both personas often flag the
same coupling from different angles — merge them, note the corroboration). Order by
leverage: what, if changed, most improves the module.

This is **propose-only** — surface the verdict and let the user decide. To act on it,
hand off to `plan-refactor` (decompose into tiny commits) or `improve-architecture`
(generate candidate redesigns).

## Output format

```markdown
## Design Review: <module / path>

**Verdict:** Sound / Refactor before building on this / Rethink the boundary

### Critical concerns
Architectural issues to resolve before more code is built on this module. Each with
location, why it matters, and the direction to take.

### Worth considering
Softer concerns the user may choose to accept.

### Long-term watch-outs
Fine today; will bend at scale or over time.

### What I'd change first
The 1-3 most leveraged changes, ranked. If the module is sound, say so plainly.
```

## Integration with other skills

- Run before a refactor to get a judgment on what's wrong; feed the verdict to
  `plan-refactor` to decompose the fix, or `improve-architecture` to generate redesigns.
- For a planning document rather than code, use `review-plan` (same agents, doc scope).
- For correctness/security/perf on a diff, use `review-code`.

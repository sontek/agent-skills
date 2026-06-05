---
name: plan-refactor
description: Create a detailed refactor plan with tiny commits via user interview. Writes the plan to a local REFACTOR_PLAN_<short-name>.md file. Use when the user asks to "plan a refactor", "create a refactor plan", "plan how to refactor", "restructure" existing code, "extract" a module, or wants tiny-commit decomposition of an existing module without changing behavior. For NEW features or phased additions, use plan-implementation instead. If Claude Code is in plan mode, plan mode itself already produces an in-conversation plan via ExitPlanMode — use review-plan on that draft instead of invoking this skill.
---

This skill is invoked when the user wants to plan a refactor. Go through the steps below. You may skip steps if you don't consider them necessary.

1. Ask the user for a long, detailed description of the problem they want to solve and any potential ideas for solutions.

2. Explore the repo to verify their assertions and understand the current state of the codebase.

3. Ask whether they have considered other options, and present other options to them.

4. Interview the user about the implementation. Be extremely detailed and thorough.

5. Hammer out the exact scope of the implementation. Work out what you plan to change and what you plan not to change.

6. Write binary **Ideal State Criteria** (ISC) — yes/no checkable conditions that define when the refactor is done. Refactors don't change behavior, so ISC for a refactor focuses on structural outcomes and anti-criteria (behavior that must remain unchanged):

   - `ISC-1: Public API surface of `auth/` module is unchanged (same exported names, same signatures)`
   - `ISC-2: All existing tests pass without modification`
   - `ISC-A-1: No new module added under `auth/` that depends on `legacy/`'s internals`

   Always write at least one anti-criterion — for refactors, "what must not change" is usually the load-bearing part.

7. Look in the codebase to check for test coverage of this area. A refactor without tests is a guess — "legacy code is simply code without tests" (Michael Feathers), and that includes code you're about to restructure. If coverage is insufficient, don't just ask the user "what are your testing plans?" — plan to *get the code under test first*, as the opening commits of the refactor:

   - **Characterization tests** pin the current behavior so the refactor can't change it silently. You don't need a spec: write an assertion you expect to fail, run it, let the failure message tell you what the code *actually* does, then change the assertion to match. Repeat per code path you'll touch. These document what the code **does**, not what it **should** do — that's exactly the safety net a behavior-preserving refactor needs.
   - **Find the seams.** A seam is a place you can alter behavior without editing there — an injectable dependency, an overridable method. If the code can't be instantiated or called under test (constructor creates its own dependencies, a static/global blocks you, a hard-to-build parameter), the early commits break that dependency *minimally* (Parameterize Constructor, Extract Interface, Extract and Override Factory Method) before any restructuring. Break just enough to get a test in.
   - **Under real time pressure**, prefer sprout/wrap over restructuring untested code: put new behavior in a new, separately-tested method or class (Sprout Method/Class), or wrap the existing call to add behavior before/after without touching its body (Wrap Method/Class). Note these as the chosen tactic in the plan.

   Make "get the target area under characterization tests" the first commit(s) in the plan whenever coverage is thin, and tie an ISC to it (e.g. `ISC-1: Characterization tests cover the public behavior of `auth/` before any structural change`).

8. Break the implementation into a plan of tiny commits. Remember Martin Fowler's advice to "make each refactoring step as small as possible, so that you can always see the program working."

9. Write a **Premortem** — 2–5 load-bearing assumptions the refactor relies on and 2–5 realistic failure modes. Ask the user whether to mitigate or accept each failure mode before committing the plan to disk.

10. Write the plan to a local file named `REFACTOR_PLAN_<short-name>.md` at the repo root (e.g., `REFACTOR_PLAN_extract-auth-middleware.md`). Use the template below.

    Don't auto-publish the plan to GitHub/JIRA/etc. If the user wants it as a GitHub issue, JIRA ticket, or team-tracker entry afterwards, they'll tell you explicitly — many repos (OSS, internal tools, solo projects) don't want an issue created just so someone can refactor.

11. After the plan file is written, offer to run the `review-plan` skill for a `senior-engineer` judgment pass (DRY, coupling, commit ordering, missed seams, ISC coverage, premortem honesty). This is the cheapest point to catch architectural mistakes — before any code is written. Apply any blocking findings by editing the plan file before starting the refactor.

Use the following template for the plan body:

<refactor-plan-template>

## Problem Statement

The problem that the developer is facing, from the developer's perspective.

## Solution

The solution to the problem, from the developer's perspective.

## Ideal State Criteria

Binary, yes/no checkable conditions that define when the refactor is done. Include explicit anti-criteria for behavior that must remain unchanged.

### Structural Outcomes
- [ ] ISC-1: ...

### Anti-Criteria
- [ ] ISC-A-1: No ...

## Commits

A LONG, detailed implementation plan. Write the plan in plain English, breaking down the implementation into the tiniest commits possible. Each commit should leave the codebase in a working state.

## Premortem

### Load-bearing assumptions
- <assumption the refactor relies on — and how we'd notice if it's wrong>

### Realistic failure modes
- <what could go wrong> — Mitigation: ... | Accepted because: ...

## Decision Document

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this refactor.

## Further Notes (optional)

Any further notes about the refactor.

</refactor-plan-template>

---
name: debug
description: >-
  Diagnose bugs scientifically: reproduce, form a hypothesis, run a falsifying experiment, identify the root cause, then fix it and add a regression test. Use for "debug this", "why isn't this working?", flaky/intermittent failures, "can't reproduce", or "find the root cause". Unlike fix-issue, debug is for cases where the cause is not yet known.
---

# Debug

> ~90% of debugging is finding and understanding the defect. The fix is usually obvious once you understand it — and ~50% of rushed fixes are wrong.

Never guess. Never apply random changes. Every action tests a hypothesis. The pressure to "just fix it" is exactly when to slow down.

## The method

```
STABILIZE → LOCATE → CHECK PRIOR FIXES → HYPOTHESIZE → EXPERIMENT → FIX → TEST → SEARCH
```

Do not jump to FIX. A fix applied before you can *predict when the bug occurs* is a guess — if you can't predict it, you don't understand it yet.

### 1. STABILIZE — get a reliable repro

You cannot debug what you cannot reproduce. Reduce to the smallest case that still fails and record the exact conditions: inputs, environment, order of operations. Intermittent failures are usually initialization order, timing/races, or stale shared state — make it predictable before going further.

### 2. LOCATE — narrow the region before hypothesizing

- **Binary search:** disable/comment out ~half the suspect code. Bug gone? It was in what you removed. Repeat. (Use for regions >~50 lines, not already-localized bugs.)
- **Check recently changed code first** — defects cluster around changes. `git log`/`git blame` the failing path; check recent deploys and config changes.
- Look for the pattern: specific data, specific user, specific environment?

### 3. CHECK PRIOR FIXES — pattern-reuse gate

Before forming a hypothesis, search the codebase for how similar bugs were handled. Has this (or a sibling) been fixed before? How do other call sites handle this situation? Is there an established pattern? Your hypothesis should account for what you find — either the pattern wasn't applied here, was applied wrong, or this is a genuinely new case.

### 4. HYPOTHESIZE — one specific, testable claim

Not "the bug is somewhere in module X." Good: "the counter isn't reset between requests because handler X shares state with Y." Use all available data (logs, stack traces, variable values). Rank competing candidates and brainstorm alternatives *before* committing to one — that's the guard against confirmation bias.

### 5. EXPERIMENT — try to *disprove* the hypothesis

Design the observation that would prove you wrong, not right.

- Add targeted logging or an assertion at the suspected site, or write a failing test that would pass *if* the hypothesis holds.
- **Observe before changing production code.** This step gathers evidence; it does not fix anything.
- Record the result, then keep or discard the hypothesis. Disproved → refine and loop back to step 4.

### 6. FIX — the root cause, not the symptom

Understand the vicinity (hundreds of lines, not just the failing line) and rule out competing hypotheses first. Save the original, make **one change at a time**. Never bolt on a special case for a specific value (`if id == 45: ...`) — that's a symptom patch that leaves the real defect live.

### 7. TEST — verify, then add a regression test

Triangulate: cases that *should* and *should not* trigger the bug, not just the original repro. Add a test that would have caught this defect, then run the full suite.

### 8. SEARCH — defects cluster

If this bug existed, similar ones likely live nearby. Search the same pattern elsewhere, the module's other methods, and code from the same author or era.

## Anti-patterns

| Pattern | Reality | Instead |
|---|---|---|
| **Shotgun debugging** — random changes until it works | You learn nothing; confidence drops | Form a hypothesis first |
| **Symptom fix** — `if client == 45: sum += 3.45` | Root cause still live, resurfaces later | Fix the algorithm |
| **Superstition** — blame the compiler/OS/"flaky machine" | Programs are deterministic; it's almost always your code | Assume the fault is yours |
| **Panic fix** under pressure | ~50% of rushed fixes are wrong | One change at a time; verify |
| **Skip verification** — fixed it, moved on | No proof it's fixed, no guard against regression | Always add the test |
| **Circular debugging** — same code, no new data | Spinning | Write down what you've ruled out; generate fresh hypotheses |

## Rule these out fast (2 minutes)

Off-by-one (`<` vs `<=`, index vs length) · null/undefined deref before a check · race condition (intermittent, timing-dependent) · uninitialized variable · operator precedence (add parens) · float equality (`==` vs epsilon) · resource leak (handle/connection/lock not released on the error path) · logic inversion (wrong branch).

## Time limits — escalate, don't grind

| Phase | Limit | Escalation |
|---|---|---|
| Quick-and-dirty | 15–30 min | Switch to the systematic method above |
| Single hypothesis | 30–60 min | Generate fresh hypotheses |
| Systematic | 2–4 hours | Take a break; rubber-duck it to a colleague |

**Confessional debugging:** explaining the problem out loud (to a person or a rubber duck) frequently surfaces the bug before you finish the sentence.

## Chain

| Situation | Next |
|---|---|
| Production error to investigate | Pull it with `sentry` first, then start at STABILIZE |
| Root cause found, fix not written yet | `fix-issue` to implement it reproduce-first |
| Root cause found, fix written | Add the regression test (step 7), then `iterate-pr` to ship |
| Defect is in untested legacy code | `plan-refactor` — get it under a characterization test before changing it |
| Fix needs structural change | `improve-architecture` / `plan-refactor` |

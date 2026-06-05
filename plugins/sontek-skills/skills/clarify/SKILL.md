---
name: clarify
description: Interview the user to resolve ambiguity in a request, plan, or design before committing to work — one targeted question at a time until intent, scope, and constraints are pinned down. Use when a request is underspecified, could have multiple valid interpretations, hides a false premise, or the user wants to stress-test a plan. Triggers on "clarify this", "grill me", "stress-test my plan", "get grilled on my design", "what am I missing", or any request vague enough that proceeding would mean guessing. Pairs with plan-implementation for pre-planning requirements clarification.
---

# Clarify

Understand what the user needs before committing to work. LLMs default to assuming rather than asking — frontier models proceed without clarification in ~70% of cases where information is missing. This skill counteracts that bias: classify what's unclear, then ask the question whose answer eliminates the most uncertainty.

Walk down each branch of the decision tree, resolving dependencies between decisions one at a time. **Ask one question per turn.** For every question, supply your own recommended answer — never make the user start from a blank page. If a question can be answered by reading the codebase, read it instead of asking.

This is a conversation, not an interrogation: think out loud *with* the user.

## Classify what's unclear

The type of gap determines the kind of question to ask.

| Fault type | What it is | Example |
|---|---|---|
| **Intention** | The real goal isn't recoverable from the request | "Make it better" — better how, for whom? |
| **Premise** | An assumption in the request is wrong | "Fix the race condition in the cache" — when no race exists |
| **Parameter** | Required details are missing or conflicting | "Build a login page" — OAuth? email/password? SSO? |
| **Expression** | The language allows more than one reading | "Clean up the API" — refactor, deprecate, or document? |

Inconsistencies *between* requirements are the hardest to catch — explicitly check whether parts of the request conflict ("keep it simple but handle every edge case").

Once you've found a gap, note which way it pulls: a term with multiple meanings → **disambiguate**; clear intent but huge scope → **specify** ("which part matters most now?"); oddly specific for the likely goal → **generalize** ("what's the broader outcome?").

## Ask the highest-information question

Don't start from "what should I ask?" Start from "what are the plausible interpretations?" — then ask the question that splits them most evenly.

1. Generate 2–4 competing interpretations of the request.
2. Identify the axis that distinguishes them.
3. Ask about that axis.

> Request: "Add caching to the API."
> A: in-memory cache for latency · B: Redis for scaling · C: HTTP cache headers for clients.
> Axis: *what problem* — speed, load, or bandwidth?
> Question: "What's driving the caching need — slow responses, high server load, or redundant client requests?"

One question on the axis of disagreement beats three on implementation details. Among candidate questions, prefer the one that splits your hypotheses ~50/50 over one that splits them 90/10 — it's more informative regardless of the answer. **Target convergence in 3–5 rounds**; past that, returns drop sharply.

When you can, show the difference instead of describing it: "Right now errors silently return null. Option A: throw and let the caller handle it. Option B: return a Result type — [snippet A] vs [snippet B]." Let the user choose on observable behavior, not abstraction.

## Match the strategy to the fault

| Strategy | When | Example |
|---|---|---|
| **Ask for a parameter** | A specific detail is missing | "What should happen when the input is empty?" |
| **Disambiguate** | Multiple valid readings exist | "By 'refactor,' do you mean restructure the module or clean up naming?" |
| **Propose alternatives** | The request is impossible as stated | "That endpoint can't paginate. Add it, or switch to cursor-based fetching?" |
| **Confirm risk** | High-stakes, irreversible action | "This drops the existing table. Proceed, or migrate the data first?" |
| **Report a blocker** | An objective barrier exists | "The API rate-limits to 100 req/s; the design needs 300. How should we handle that?" |

## Effort awareness — ask about intent, figure out the rest yourself

Estimate what each question costs the user, and route accordingly:

- **Low** ("async or sync?") — the user already knows. Ask freely.
- **Medium** ("expected request volume?") — the user might not know. Ask only if it changes the design.
- **High** ("what does the upstream service return on timeout?") — don't ask; investigate.

The principle: **ask about intent, goals, and constraints — the user's knowledge. Determine implementation details from the code — your job.**

## Every question passes these checks

Focused (one gap, no compound questions) · Answerable (from what the user already knows) · Discriminative (the answer narrows interpretations) · Non-leading (doesn't presuppose its answer) · Task-relevant.

## Confirmatory mode — when the user says "just do it"

If the user signals "just do it," "whatever works," answers a multi-part question with one word, or goes terse, **don't go silent — switch to confirmatory.** Keep asking the questions you need, but supply your best-guess answer and let the user veto:

| Exploratory | Confirmatory |
|---|---|
| "What should empty input do?" | "I'm assuming empty input returns 400 with a validation error — correct?" |
| "Async or sync?" | "This looks I/O-bound, so I'll make it async unless you say otherwise." |

The completeness bar usually doesn't change; only the user's typing cost drops. Read the room each turn — a detailed, engaged answer means switch back to exploratory.

**Honest exception:** on genuinely low-stakes, easily-reversible calls, "just do it" can mean the user is trading rigor for speed — drop the question entirely rather than manufacturing confirmations. For high-stakes calls (irreversible, security, data loss, architectural lock-in) keep every question, just confirmatory. When uncertain, prefer confirmatory over silent assumption.

## Track the state

Hold two sets as the conversation moves: **confirmed** (interpretations/constraints/goals the user validated) and **ruled out** (rejected, or contradicted by confirmed items). Score remaining interpretations by fit with confirmed and conflict with ruled-out — the space narrows each turn. Stop when no competing hypothesis meaningfully survives.

## Anti-patterns

| Pattern | Instead |
|---|---|
| Proceeding without checking | Run the classification pass first |
| Asking implementation details | Figure them out from the codebase |
| Rapid-fire question lists | One question per turn |
| Asking what you could read from code | Read first; ask only what code can't tell you |
| Over-asking on a clear request | If it's clear, proceed |
| Abstract questions | Show differential examples |
| Going silent on "just do it" | Switch to confirmatory, state the assumption |
| One round and done | Continue until hypotheses converge |

## Chain

- Use **before** writing a plan to nail down fuzzy intent, then hand off to `plan-implementation` or `plan-refactor`.
- Use `review-plan` *after* a plan is written for a judgment pass; `clarify` is the *upfront* counterpart.
- New ambiguity surfacing mid-work → re-enter the clarify loop.

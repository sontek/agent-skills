---
name: review-perf
description: General application performance review for non-Django code (Flask, FastAPI, Go, Node, generic Python). Use when asked to "review performance", "audit performance", "find slow code", "perf review", or audit app-tier code for blocking I/O on async paths, algorithmic blow-ups, per-item network loops, unbounded memory accumulation, or missing application caching. Find-only — use `optimize-perf` to apply fixes with benchmarks. Covers the application surface that `review-django-perf` (Django ORM) and `sql-reviewer` (raw SQL / migrations) do not. Validation-first — no flag without traced evidence.
allowed-tools: Read, Grep, Glob, Bash, Task
license: LICENSE
---

# Review Performance

Route an application-tier performance review through the `perf-reviewer` agent in isolated context. The skill resolves scope and forwards grounding; the agent validates each issue through code tracing before reporting.

## When to invoke

- "Review performance", "audit performance", "find slow code", "perf review", "perf pass on this branch"
- Pre-merge perf pass on Flask / FastAPI / Go / Node / plain Python application code
- Audit of a specific service or worker for latency or memory regressions

This skill is **find-only** — it returns findings, it does not apply fixes. For "optimize this", "make this faster", or "speed this up" (i.e. apply and measure), use `optimize-perf` directly.

Don't use for:

- Django ORM perf — use `review-django-perf`
- Raw SQL / SQLAlchemy / migration perf — use `review-code` (it dispatches `sql-reviewer`)
- Generic code review — use `review-code`
- Applying perf fixes with benchmarks — use `optimize-perf`

## Modes

Pick one before invoking. Default to `branch` if unspecified.

- **`branch` (default)** — Review changes vs. the main branch. Agent flags only issues introduced by the diff.
- **`paths`** — Review the current state of an explicit list of files or directories. Requires a path list from the caller.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`). Compute diff range as `<base>...HEAD`. Collect changed application files with `git diff --name-only <base>...HEAD`. Filter out files in `*/migrations/`, `*/tests/`, and `*.sql` — those belong to other reviewers.
- **`paths` mode:** take the explicit file/directory list from the caller.

### 2. Ground the review

Light pass for context-forwarding only. Do NOT validate performance issues yourself.

- Note the framework (Flask / FastAPI / Go net+http / gin / express / asyncio / sync), since framework choice gates the blocking-I/O finding.
- Note which endpoints / workers / scripts are in scope.
- Capture caller-supplied volume hints ("this endpoint serves 5k rps", "this worker processes batches of 100k", "this is internal-only / low traffic") — the agent needs these to size impact.

### 3. Delegate to the perf-reviewer agent

Invoke via the Task tool with `subagent_type: agent-skills:perf-reviewer`. Include in the prompt:

- The **mode** (`branch` or `paths`).
- For `branch` mode: base branch and diff range.
- For `paths` mode: the explicit path list.
- Framework, traffic, and volume hints from the caller — verbatim.

Example prompt skeleton:

```
Run an application-tier performance review in `branch` mode.

Base branch: main
Diff range: main...HEAD
Changed files:
- app/api/orders.py
- app/workers/sync.py

Framework: FastAPI (async). Traffic: /orders/* is on the checkout path.
Caller hints:
- Sync worker processes ~10k orders/run, runs hourly.
- /orders/{id}/status is the hottest read endpoint.

Follow your rubric: stay in your lane (application tier — no Django ORM, no raw SQL),
validate each issue (trace flow, check existing caches/batches, confirm hot path),
and only flag with evidence. Zero findings is acceptable.
```

### 4. Return the agent's output

Pass the agent's findings back to the caller verbatim. Don't summarize, re-prioritize, or filter.

For follow-up ("explain the batching fix", "estimate latency reduction"), invoke the agent again with the relevant context.

---
name: review-django-perf
description: Django performance code review. Use when asked to "review Django performance", "find N+1 queries", "optimize Django", "check queryset performance", "database performance", "Django ORM issues", or audit Django code for performance problems.
allowed-tools: Read, Grep, Glob, Bash, Task
license: LICENSE
---

# Review Django Performance

Route a Django performance review through the `django-perf-reviewer` agent in isolated context. The skill resolves scope and forwards grounding; the agent validates each issue through code tracing before reporting.

## When to invoke

- "Review Django performance", "find N+1 queries", "optimize Django", "check queryset performance"
- Pre-merge performance pass on Django views, viewsets, serializers, or ORM-heavy code
- Audit of a specific app/module for query-count or memory regressions

Don't use for:

- Django access control / IDOR — use `review-django-access`
- Generic code review — use `review-code`
- Security review — use `review-security`

## Modes

Pick one before invoking. Default to `branch` if unspecified.

- **`branch` (default)** — Review changes vs. the main branch. Agent flags only issues introduced by the diff.
- **`paths`** — Review the current state of an explicit list of files or directories. Requires a path list from the caller.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`). Compute diff range as `<base>...HEAD`. Collect changed Python/template files with `git diff --name-only <base>...HEAD -- '*.py' '*.html'`.
- **`paths` mode:** take the explicit file/directory list from the caller.

### 2. Ground the review

Light pass for context-forwarding only. Do NOT validate performance issues yourself.

- Note which views/serializers are in scope and their model dependencies.
- Capture caller-supplied data-volume hints ("this table has 1M+ rows", "this endpoint is internal-only / low traffic") — the agent needs these to size impact.

### 3. Delegate to the django-perf-reviewer agent

Invoke via the Task tool with `subagent_type: agent-skills:django-perf-reviewer`. Include in the prompt:

- The **mode** (`branch` or `paths`).
- For `branch` mode: base branch and diff range.
- For `paths` mode: the explicit path list.
- Data-volume and traffic hints from the caller — verbatim.

Example prompt skeleton:

```
Run a Django performance review in `branch` mode.

Base branch: main
Diff range: main...HEAD
Changed files:
- app/api/views.py
- app/api/serializers.py
- app/templates/users.html

Caller hints:
- User table: ~500k rows in production.
- /api/users/ endpoint is on the homepage hot path.

Follow your rubric: validate each issue (trace flow, check existing optimizations,
verify volume, confirm hot path) before reporting. Zero findings is acceptable.
```

### 4. Return the agent's output

Pass the agent's findings back to the caller verbatim. Don't summarize, re-prioritize, or filter.

For follow-up ("explain the prefetch fix", "estimate query reduction"), invoke the agent again with the relevant context.

---
name: review-django-access
description: 'Django access control and IDOR security review. Use when reviewing Django views, DRF viewsets, ORM queries, or any Python/Django code handling user authorization. Trigger keywords: "IDOR", "access control", "authorization", "Django permissions", "object permissions", "tenant isolation", "broken access".'
allowed-tools: Read, Grep, Glob, Bash, Task
license: LICENSE
---

# Review Django Access Control

Route a Django IDOR / authorization review through the `django-access-reviewer` agent in isolated context. The skill resolves scope and forwards grounding; the agent investigates the authorization model, traces flows, and reports HIGH-confidence findings.

## When to invoke

- "Review for IDOR", "check access control", "audit authorization", "find broken access"
- Pre-merge security pass on Django views, DRF viewsets, or any code that fetches user-owned data
- Tenant-isolation audit on multi-tenant Django code

Don't use for:

- Generic security review (XSS, SQLi, SSRF) — use `review-security` (routes to `security-auditor`)
- Django performance review — use `review-django-perf`
- General code review — use `review-code`

## Modes

Pick one before invoking. Default to `branch` if unspecified.

- **`branch` (default)** — Review changes vs. the main branch. Agent flags only issues introduced by the diff.
- **`paths`** — Review the current state of an explicit list of files or directories. Requires a path list from the caller.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`). Compute diff range as `<base>...HEAD`. Collect changed Python files with `git diff --name-only <base>...HEAD -- '*.py'`.
- **`paths` mode:** take the explicit file/directory list from the caller.

### 2. Ground the review

Light pass for context-forwarding only. Do NOT investigate authorization yourself.

- Identify the ownership/tenant model from a quick model file scan (`grep -rn "owner\|user_id\|organization\|tenant" --include='models.py' | head`).
- Note the base view class convention (DRF `viewsets.ModelViewSet`, Django `View`, custom base class).
- Capture any caller-supplied "this endpoint is internal-only" or "this resource is intentionally public" notes.

### 3. Delegate to the django-access-reviewer agent

Invoke via the Task tool with `subagent_type: agent-skills:django-access-reviewer`. Include in the prompt:

- The **mode** (`branch` or `paths`).
- For `branch` mode: base branch and diff range.
- For `paths` mode: the explicit path list.
- Ownership/tenant signals you collected.
- Caller-supplied trust-boundary notes — verbatim.

Example prompt skeleton:

```
Run a Django access-control review in `branch` mode.

Base branch: main
Diff range: main...HEAD
Changed Python files:
- app/api/views.py
- app/api/serializers.py

Ownership signals: Models use `organization_id` for tenant scoping;
base class is `OrgScopedViewSet` (see app/api/base.py).

Caller notes:
- `/public/*` routes are intentionally unauthenticated.

Follow your rubric: understand the authorization model first, map attack surface,
trace specific flows end-to-end, report HIGH-confidence findings only.
```

### 4. Return the agent's output

Pass the agent's findings back to the caller verbatim. Don't summarize, re-prioritize, or filter.

For follow-up ("explain finding #2 in more depth", "propose the fix"), invoke the agent again with the relevant context rather than answering from your own judgment.

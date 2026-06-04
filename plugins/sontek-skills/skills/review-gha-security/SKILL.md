---
name: review-gha-security
description: 'GitHub Actions security review for workflow exploitation vulnerabilities. Use when asked to "review GitHub Actions", "audit workflows", "check CI security", "GHA security", "workflow security review", or review .github/workflows/ for pwn requests, expression injection, credential theft, and supply chain attacks. Exploitation-focused with concrete PoC scenarios.'
allowed-tools: Read, Grep, Glob, Bash, Task
---

<!--
Attack patterns and real-world examples sourced from the HackerBot Claw campaign analysis
by StepSecurity (2025): https://www.stepsecurity.io/blog/hackerbot-claw-github-actions-exploitation
-->

# Review GitHub Actions Security

Route a GHA workflow security review through the `gha-security-reviewer` agent in isolated context. The skill resolves scope and forwards grounding; the agent reads the workflows, loads attack-pattern references, and produces HIGH-confidence findings with PoCs.

## When to invoke

- "Review GitHub Actions", "audit workflows", "check CI security", "GHA security"
- Pre-merge audit of `.github/workflows/` changes
- Spot-check of an externally-triggered workflow (`pull_request_target`, `issue_comment`)

Don't use for:

- Generic security review — use `review-security`
- Generic code review — use `review-code`
- Application access control / IDOR — use `review-django-access`

## Modes

Pick one before invoking. Default to `branch` if unspecified.

- **`branch` (default)** — Review changes vs. the main branch. Agent flags only workflow vulnerabilities introduced by the diff.
- **`paths`** — Review the current state of an explicit list of workflow files. Requires a path list from the caller.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`). Compute diff range as `<base>...HEAD`. Collect changed workflow files with `git diff --name-only <base>...HEAD -- '.github/workflows/*' '.github/actions/**/action.yml' 'action.yml'`.
- **`paths` mode:** take the explicit file/directory list from the caller.

### 2. Ground the review

Light pass for context-forwarding only. Do NOT analyze workflows yourself.

- Note which triggers appear in scope (`pull_request_target`, `issue_comment`, `pull_request`, `push`, etc.). The agent uses this to decide which attack-pattern references to load.
- Capture caller-supplied repo-level mitigation notes ("we have org-level OIDC required", "branch protection blocks force-push").

### 3. Delegate to the gha-security-reviewer agent

Invoke via the Task tool with `subagent_type: sontek-skills:gha-security-reviewer`. Include in the prompt:

- The **mode** (`branch` or `paths`).
- For `branch` mode: base branch and diff range.
- For `paths` mode: the explicit path list.
- Trigger signals you collected (which references to prioritize loading).
- Caller-supplied repo-level mitigation notes — verbatim.

Example prompt skeleton:

```
Run a GitHub Actions security review in `branch` mode.

Base branch: main
Diff range: main...HEAD
Changed workflow files:
- .github/workflows/release.yml
- .github/workflows/ci.yml

Trigger signals: release.yml uses pull_request_target (load pwn-request.md);
ci.yml uses pull_request only.

Caller notes:
- Org-level required: all third-party actions must be SHA-pinned.
- No self-hosted runners in this repo.

Follow your rubric: threat model is external attacker without write access,
report only HIGH/MEDIUM confidence with full PoC, validate the attack path
before reporting.
```

### 4. Return the agent's output

Pass the agent's findings back to the caller verbatim. Don't summarize, re-prioritize, or filter.

For follow-up ("walk me through the PoC", "propose the env-var fix"), invoke the agent again with the relevant context.

## Reference materials

The attack-pattern reference library under `references/` is consumed by the `gha-security-reviewer` agent (see its "Step 1" section for the full index). The skill itself does not load these — it just signals which triggers apply so the agent can load them.

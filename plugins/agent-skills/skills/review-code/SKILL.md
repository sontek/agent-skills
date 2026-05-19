---
name: review-code
description: Perform code reviews and find bugs/security issues with prioritized, actionable findings. Use when reviewing pull requests, examining code changes, finding bugs, auditing for vulnerabilities, or providing feedback on code quality. Supports two modes — `branch` (default, reviews diff vs. main) and `paths` (reviews an explicit file/dir list as-is, ignoring git history). Covers correctness, performance, security, design, testing, and cross-cutting concerns.
---

# Review Code

Route a code review through the `code-reviewer` agent in isolated context. The skill resolves scope and forwards useful grounding; the agent reads the code and produces the findings.

## When to invoke

- "Review the code", "review this PR", "review this branch", "find bugs in this diff"
- Pre-merge code review on a feature branch
- Audit a specific set of files or directories for quality / correctness issues

Don't use for:

- Reviewing a planning document — use `review-plan`
- Security-only deep dives — use `review-security` (which routes to `security-auditor`)
- Reviewing skills authored under `plugins/agent-skills/skills/` — use `review-skill`

## Modes

Pick one before invoking. If the caller didn't specify, default to `branch`.

- **`branch` (default)** — Review the current branch's changes vs. the main branch. Agent flags only issues introduced by the diff and emits a Human Reviewer Callouts section.
- **`paths`** — Review the current state of an explicit list of files or directories, regardless of git history. Agent flags any issue in the reviewed code. Requires a path list from the caller — do not default to whole-repo.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`; check `git symbolic-ref refs/remotes/origin/HEAD` or look for an explicit override in conversation). Compute the diff range as `<base>...HEAD`. Collect the changed file list with `git diff --name-only <base>...HEAD`.
- **`paths` mode:** take the explicit file/directory list from the caller. If they didn't provide one, ask before invoking.

### 2. Ground the review

Do a light pass to package useful context for the agent. Do NOT perform the review yourself.

- Read the PR description / branch summary if available (`gh pr view --json title,body` when there's an open PR for the branch).
- Capture any caller-supplied "don't flag this, it's intentional" notes from the conversation.
- Note presence of `REVIEW_GUIDELINES.md` (the agent will load it; just confirm it's there).

### 3. Delegate to the code-reviewer agent

Invoke via the Task tool with `subagent_type: agent-skills:code-reviewer`. The agent has isolated context, so the prompt must be self-contained. Include:

- The **mode** (`branch` or `paths`).
- For `branch` mode: the base branch name and the diff range.
- For `paths` mode: the explicit path list.
- The PR description / branch summary if you found one.
- Any caller-supplied "don't flag X, it's intentional" notes — verbatim.
- A pointer to `REVIEW_GUIDELINES.md` if one exists.

Example prompt skeleton:

```
Run a code review in `branch` mode.

Base branch: main
Diff range: main...HEAD
Changed files:
- path/to/file.py
- path/to/other.py

PR description:
<paste branch summary>

Caller notes (don't flag these — intentional):
- <note 1>
- <note 2>

Project guidelines: REVIEW_GUIDELINES.md exists at repo root — load it.

Follow your rubric: investigation approach, what-to-flag, review checklist, fail-fast, priority levels, output format including Human Reviewer Callouts.
```

### 4. Return the agent's output

Pass the agent's findings back to the caller verbatim. Don't summarize, re-prioritize, or filter — that defeats the independent-review value.

If the caller wants follow-up (e.g., "explain finding #2 in more depth", "apply finding #1"), invoke the agent again with the relevant context rather than answering from your own judgment.

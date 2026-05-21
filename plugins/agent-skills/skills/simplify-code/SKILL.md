---
name: simplify-code
description: Review changed code for AI-generated slop and apply fixes. Use when the user says "simplify", "clean this up", "deslop", "tidy up", or after AI-generated code lands. Delegates to the curated code-simplifier agent, which applies an AI-slop rubric the built-in /simplify command doesn't.
---

# Simplify Code

Route a slop-detection pass through the `code-simplifier` agent in isolated context, then apply its findings. The skill resolves which code to review and forwards grounding; the agent reads the code against the curated AI-slop rubric and returns per-file fixes.

Use this instead of Claude Code's built-in `/simplify`, which spawns generic review agents without the curated rubric. A bare `/simplify` runs the built-in; this skill is reached by natural language ("simplify this", "clean this up") or by its plugin-qualified name `/agent-skills:simplify-code`.

## Phase 1 — Identify Changes

Resolve the scope to simplify, in this order:

```bash
git diff                 # unstaged working-tree changes
git diff HEAD            # include staged changes
git diff --name-only HEAD
```

- If the diff is non-empty, that's the scope.
- If the working tree is clean, fall back to files edited in the current conversation.
- If neither exists, ask the user what to simplify. Don't default to the whole repo.

Capture the explicit file list or diff range — the agent runs in isolated context and sees only what you pass it.

## Phase 2 — Delegate to the code-simplifier agent

Invoke via the Task tool with `subagent_type: agent-skills:code-simplifier`. The prompt must be self-contained:

- The **scope** — the explicit file list, or the diff range plus changed files.
- Any user-supplied "don't flag X, it's intentional" notes — **verbatim**.
- A pointer to `CLAUDE.md` / `AGENTS.md` if present (the agent loads them for project standards).

Example prompt skeleton:

```
Simplify the following changed code.

Scope (files in the current diff):
- path/to/changed.py
- path/to/other.py

Project standards: CLAUDE.md and AGENTS.md exist at repo root — load them.

Caller notes (don't flag these — intentional):
- the retry wrapper in client.py is a deliberate instrumentation boundary

Run your full AI Slop Detection Rules pass. Return per-file fixes with rule IDs.
```

Do not perform the simplification yourself — the agent owns the rubric.

## Phase 3 — Apply Findings

The agent returns per-file fixes tagged with rule IDs. For each:

- **Apply low-risk fixes directly** — anything behavior-preserving where existing tests are the regression guard: slop comments, rationale-narrating docstrings (`comments.docstring-rationale`), change-narration comments (`comments.change-narration`), labeled TODOs (`comments.template-comments`), trivial wrappers, defensive `try/catch` with no semantic loss.
- **Flag higher-risk fixes for user confirmation** — anything that could change semantics: inlining a helper called from production code, swapping a public-function type annotation, or any change where you can't prove behavior is preserved. State the precise before → after and the call sites affected; let the user decide.
- **Dismiss false positives** with a one-line rationale, then move on. Don't argue the rule — the agent over-flags by design; pruning is your job.

Report what was applied and what was flagged in a short summary. No per-finding narration during the pass.

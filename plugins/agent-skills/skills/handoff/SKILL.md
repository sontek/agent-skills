---
name: handoff
description: Write a structured handoff document so a fresh Claude Code session can continue the current work without re-reading the entire transcript. Use when asked to "hand off", "handoff", run "/handoff", prepare for a "/clear", start a fresh session without losing context, or save the current conversation's state for a future session. Produces a local `HANDOFF_<slug>.md` (or `/tmp/HANDOFF_<slug>.md` outside a repo) that the user pastes or opens in the new session.
---

# Handoff

Capture the load-bearing context from the current conversation into a
structured `HANDOFF_<slug>.md` so a fresh session can pick up cleanly.
Used before `/clear`, before opening a new Claude Code session, or
whenever context window pressure is forcing a reset.

## When to invoke

- User says "hand off", "handoff", "/handoff", "prep for /clear",
  "continue in a fresh session", "save context"
- Conversation is approaching context compaction and the user wants
  control over what survives
- A long planning/debugging session needs to pause and resume cleanly

Don't use for:

- Persisting reusable preferences — use the memory system instead
- Writing a plan from scratch — use `plan-implementation` or
  `plan-refactor`
- Summarizing what was done for a PR description — write the PR body

## Inputs

The user usually provides a continuation prompt:

```text
/handoff <what the fresh session should do next>
```

If they didn't, identify it from the conversation: what's the next
concrete step they'd want a fresh session to take? If it's genuinely
ambiguous, ask one short question before writing — otherwise make the
reasonable call and continue.

## Workflow

1. Pick a short kebab-case slug for the work, e.g. `auth-cleanup`,
   `release-fix`, `flaky-test-triage`.
2. Decide the file location:
   - In a git repo: `HANDOFF_<slug>.md` at repo root.
   - Outside a repo: `/tmp/HANDOFF_<slug>.md`.
3. Write the file using the template below.
4. Print the path and tell the user to start a fresh Claude Code
   session and paste the file's contents (or open the file and ask the
   new session to read it).
5. Stop. Do not continue the actual work in the current session.

## Template

```markdown
# Handoff: <short title>

## Continuation Prompt
<the user's exact next-step prompt, verbatim>

## Current Goal
<what we're trying to accomplish overall — one paragraph>

## What Happened
- <important actions already taken in this session>
- <files created / edited / read if relevant>
- <commands run and meaningful results>

## Decisions and Rationale
- <decision> — <why>

## Current State
- <what is true right now>
- <uncommitted changes / branch / PR state / running processes>
- <open todo list state if relevant>

## Important Context
- <constraints, conventions, user preferences picked up in this session>
- <links to relevant files, plan documents, PRs, issues>

## Risks / Gotchas
- <things the next session must not miss>
- <known wrong turns to avoid repeating>

## Suggested Next Steps
1. <first concrete step>
2. <second concrete step>
3. <third concrete step>
```

## Rules for writing the handoff

- **No secrets.** Redact tokens, passwords, API keys, private URLs, or
  any credential that appeared in the transcript. If a secret was
  central to the work, write `<redacted: <description>>` so the next
  session knows to retrieve it themselves.
- **No invented details.** If a detail is uncertain, say so
  explicitly (`uncertain — last seen ~10 messages ago`). Don't paper
  over gaps.
- **Precise references over vague statements.** File paths, command
  names, branch names, PR numbers, error text, function names — not
  "the auth file" or "that error".
- **High signal, not transcript dump.** Aim for a doc the next session
  reads in under a minute. Skip blow-by-blow back-and-forth; keep
  decisions and current state.
- **Omit sections with no substance.** If there are no risks, drop the
  Risks heading rather than writing "None".

## Launching the fresh session

After writing the file:

1. Print the absolute path.
2. Tell the user to either:
   - Run `/clear` in this same Claude Code session, then paste the file
     contents as the first message of the cleared session, **or**
   - Open a new Claude Code window in the same project and start with
     `Read <path>. Continue from this handoff.` as the first message.
3. Do not continue the actual work in this session — that defeats the
   purpose.

## Final response from the current session

Keep it short:

- The handoff file path.
- A one-line summary of what's in it.
- Instructions to `/clear` (or open a new window) and read the file.
- Nothing else.

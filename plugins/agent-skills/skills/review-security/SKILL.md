---
name: review-security
description: Security code review for vulnerabilities. Use when asked to "review security", "security review", "find vulnerabilities", "check for security issues", "audit security", "OWASP review", or review code for injection, XSS, authentication, authorization, cryptography issues. Provides systematic review with confidence-based reporting.
allowed-tools: Read, Grep, Glob, Bash, Task
license: LICENSE
---

<!--
Reference material based on OWASP Cheat Sheet Series (CC BY-SA 4.0)
https://cheatsheetseries.owasp.org/
-->

# Review Security

Route a security review through the `security-auditor` agent in isolated context. The skill resolves scope and forwards useful grounding; the agent reads the code, loads OWASP references, and produces HIGH-confidence findings.

## When to invoke

- "Review security", "security review", "find vulnerabilities", "check for SSRF/IDOR/SQLi"
- Pre-launch security check on a feature or branch
- Audit a specific set of files for security issues

Don't use for:

- General code review (correctness, style, design) — use `review-code`
- CI/CD-specific deep dive on `.github/workflows/` — use `review-gha-security`
- Django access-control deep dive — use `review-django-access`

## Modes

Pick one before invoking. Default to `branch` if unspecified.

- **`branch` (default)** — Review changes vs. the main branch. Agent flags only issues introduced by the diff.
- **`paths`** — Review the current state of an explicit list of files or directories. Requires a path list from the caller — do not default to whole-repo.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`; check `git symbolic-ref refs/remotes/origin/HEAD` or honor an explicit override). Compute diff range as `<base>...HEAD`. Collect changed files with `git diff --name-only <base>...HEAD`.
- **`paths` mode:** take the explicit file/directory list from the caller. If they didn't provide one, ask before invoking.

### 2. Ground the review

Light pass to package useful context for the agent. Do NOT perform the security review yourself.

- Identify code type (API endpoints, frontend, file handling, crypto, deserialization, external requests, CI/CD config) so the agent knows which OWASP references to load.
- Identify language/framework from file extensions and imports.
- Capture any caller-supplied "this entry point is internal-only" or "this is server-controlled" notes.

### 3. Delegate to the security-auditor agent

Invoke via the Task tool with `subagent_type: agent-skills:security-auditor`. The agent has isolated context, so the prompt must be self-contained. Include:

- The **mode** (`branch` or `paths`).
- For `branch` mode: base branch and diff range.
- For `paths` mode: the explicit path list.
- Code-type and language signals you collected (so the agent loads the right references).
- Any caller-supplied trust-boundary notes — verbatim.

Example prompt skeleton:

```
Run a security audit in `branch` mode.

Base branch: main
Diff range: main...HEAD
Changed files:
- path/to/views.py
- path/to/upload.py

Code type signals: API endpoints (load authorization.md, injection.md), file uploads (load file-security.md).
Language: Python / Django (load languages/python.md).

Caller notes (trust boundary):
- `/internal/*` routes are behind VPN — treat as internal-only.

Follow your rubric: research before reporting, confidence-gate everything, output HIGH-confidence findings with full PoCs.
```

### 4. Verify before returning (independent backstop)

The `security-auditor` already self-gates to HIGH confidence via its 5-part exploit model, so this is a light backstop, not a re-review — and it's still independent (a separate fresh agent, not your own judgment). If the auditor returned any findings, dispatch the **`finding-verifier`** agent (`subagent_type: agent-skills:finding-verifier`) once on them: pass each finding's fingerprint, claimed mechanism and consequence, and the diff scope, but **not** the auditor's reasoning. **Drop only REFUTED** findings — the ones the verifier proved wrong from the code (input that isn't actually attacker-controlled, a framework protection already in place). Keep CONFIRMED and PLAUSIBLE untouched. For a PLAUSIBLE finding whose `needs_confirmation` names a trust-boundary fact you can't see from code, surface the question alongside the finding rather than dropping it. Skip this step entirely if the auditor returned no findings.

### 5. Return the output

Pass the surviving findings back to the caller verbatim — minus anything the verifier refuted in step 4. Don't summarize, re-prioritize, or filter on your own judgment; the verifier's REFUTED calls are the only filter applied.

If the caller wants follow-up (e.g., "explain the exploit", "propose the fix"), invoke the agent again with the relevant context rather than answering from your own judgment.

## Reference materials

The OWASP-derived reference library under `references/`, `languages/`, and `infrastructure/` is consumed by the `security-auditor` agent (see its "Reference materials" section for the full index). The skill itself does not load these — it just signals which categories apply so the agent can load them.

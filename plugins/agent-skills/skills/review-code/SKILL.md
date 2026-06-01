---
name: review-code
description: Multi-reviewer code review of changes you're working on — fans out to specialized review sub-agents (code, security, Django access/perf, GitHub Actions), coalesces their findings, and returns one prioritized, deduplicated report. Use when reviewing your own branch/diff: "review my changes", "review this branch", "review this diff", "find bugs in this code", "audit these files". Two modes — `branch` (default, diff vs main) and `paths` (explicit file/dir list). Covers correctness, performance, security, design, testing. To leave comments on someone else's PR use review-pr; to auto-apply fixes use auto-review-code; for a plan use review-plan.
allowed-tools: Read, Grep, Glob, Bash, Task
---

# Review Code

Fan out to the specialized review agents in isolated context, coalesce their findings, and return one prioritized report. The skill resolves scope and selects reviewers; the agents read the code and produce the findings. Use this on code you're working on, to read or hand to `auto-review-code` for fixes. For comments on someone else's PR, use `review-pr` (human-toned comments + approval-to-post).

## When to invoke

- "Review my changes", "review this branch", "review this diff", "find bugs in this code"
- Pre-merge review of your own feature branch
- Audit a specific set of files or directories for quality / correctness issues

Don't use for:

- Leaving review comments on someone else's PR — use `review-pr`
- Auto-applying fixes in a loop — use `auto-review-code`
- Reviewing a planning document — use `review-plan`
- Reviewing skills under `plugins/agent-skills/skills/` — use `review-skill`

## Modes

Pick one before invoking. If the caller didn't specify, default to `branch`.

- **`branch` (default)** — Review the current branch's changes vs. the main branch. Agents flag only issues introduced by the diff.
- **`paths`** — Review the current state of an explicit list of files or directories, regardless of git history. Requires a path list from the caller — do not default to whole-repo; ask if it's missing.

## Process

### 1. Resolve scope

- **`branch` mode:** determine the base branch (default `main`; check `git symbolic-ref refs/remotes/origin/HEAD` or an explicit override in conversation). Diff range `<base>...HEAD`. Collect changed files: `git diff --name-only <base>...HEAD`.
- **`paths` mode:** take the explicit file/directory list from the caller.

### 2. Pick reviewers from the changed files

Always dispatch **`code-reviewer`** and **`security-auditor`**. Add specialists only when the changed files touch their domain — running one with nothing in scope just adds noise:

| Signal in changed files | Add agent |
|---|---|
| Django code (`models.py`, `views.py`, `urls.py`, DRF, `from django`) | `django-access-reviewer`, `django-perf-reviewer` |
| Application-tier code in any backend stack — Flask, FastAPI, Starlette, **Django views/services/tasks/workers**, Go `net/http` / gin / echo, Node express / fastify, plain Python services/workers | `perf-reviewer` |
| `.github/workflows/*.yml` | `gha-security-reviewer` |
| IaC (`*.tf`, `*.tofu`, `infra/`) | `iac-reviewer` |
| DB layer (migrations, raw SQL, `import sqlalchemy`/`sqlmodel`, `cursor.execute`/`text(`) | `sql-reviewer` |

`sql-reviewer` and `django-perf-reviewer` can both match a Django-ORM diff that also touches raw SQL; dispatch both — the coalesce step (5) deduplicates and treats agreement as corroboration. The same applies to `perf-reviewer` co-firing with `django-perf-reviewer` or `sql-reviewer` — including on Django code, where all three may run. `perf-reviewer` leads with the application tier (algorithmic / async / batching / caching) but also surfaces the **language-agnostic** shapes that cross into the data layer — a per-item round-trip in a loop (including DB writes), an unbounded fetch into memory — naming the generic problem and fix; the data-layer reviewers own the exact idiom (`bulk_update` vs `update`, index DDL, locking). When they land the same finding, dedup collapses it and treats the agreement as corroboration. Don't suppress `perf-reviewer` on Django code to avoid the overlap — the overlap is the backstop.

### 3. Ground the review

Light pass only — do NOT review the code yourself.

- Read the branch summary / PR description if available (`gh pr view --json title,body` when a PR exists).
- **Claims audit.** When the PR description states concrete numbers, defaults, or behavioral claims ("defaults to 8 GB", "lowers the timeout to 30s", "now retries 3 times"), spot-check them against the diff and forward any mismatch to the agents as a candidate finding — the description may describe an earlier revision. Don't audit prose intent, only checkable claims.
- Capture any caller "don't flag this, it's intentional" notes verbatim.
- Note whether `REVIEW_GUIDELINES.md` exists (the agents load it; just confirm it's there).

### 4. Dispatch in parallel

Invoke every selected agent in a **single message with multiple Task calls** so they run concurrently. Use `subagent_type: agent-skills:<agent-name>`. Each prompt is self-contained (isolated context): include the mode, the base branch + diff range (or path list), the changed-file list, the grounding from step 3, the caller's "don't flag X" notes verbatim, and a pointer to `REVIEW_GUIDELINES.md` if present. Tell each agent to follow its own rubric and output format.

### 5. Coalesce, normalize, and report

Merge the raw findings into one deduplicated report:

- **Dedup / corroborate.** Same file within ±3 lines on the same root issue → one entry; note when multiple reviewers raised it (corroboration raises confidence and ordering).
- **Drop noise.** In `branch` mode, drop findings outside the diff.
- **Normalize severity to one ruler.** Each agent uses its own scale; map them onto a shared `P0`–`P3` band so the report sorts cleanly and downstream tooling (e.g. `auto-review-code`) can triage uniformly. This is scale-mapping, not second-guessing — keep each agent's native label in the line.
- **Don't re-review.** Trust each agent's call; your job is consolidation, not a fresh opinion.

The IaC and SQL reviewers already emit `P0`–`P3`, so their bands carry over directly.

| Source severity | Normalized |
|---|---|
| code-reviewer `[P0]`; security / GHA **Critical**; access bypass enabling cross-user/tenant data read or write; sql-reviewer `[P0]` (injection reachable from untrusted input) | **P0** |
| code-reviewer `[P1]`; security / GHA **High**; other IDOR / access-control gaps; Django perf **CRITICAL** (N+1, unbounded queryset); perf-reviewer `[P1]` (blocking I/O on async path, algo blow-up, per-item network loop, unbounded memory); iac / sql-reviewer `[P1]` (apply-failure, migration/DDL or transaction corruption) | **P1** |
| code-reviewer `[P2]`; security / GHA **Medium** or "Needs verification"; Django perf **HIGH** (missing index, write loop); perf-reviewer `[P2]` (missing app cache, misused concurrency); iac / sql-reviewer `[P2]` | **P2** |
| code-reviewer `[P3]`; perf-reviewer `[P3]` (micro-inefficiency); iac / sql-reviewer `[P3]`; anything advisory | **P3** |

Carry "Needs verification" findings through at their normalized band with the verification question intact — don't silently drop them.

Output: group by normalized priority (P0 first), one finding per line, anchored and fingerprint-shaped:

```
[P0] path/to/file.py:42 | security | sql-injection-in-search — security-auditor (Critical, HIGH confidence)
[P1] path/to/views.py:88 | access  | idor-order-detail        — django-access-reviewer (High)
```

The `file:line | category | slug` portion is a stable fingerprint downstream tools rely on. Keep `branch`-mode Human Reviewer Callouts as a trailing section. For follow-up ("explain #2", "go deeper on the security findings"), re-invoke the relevant agent rather than answering from your own judgment.

## What this review optimizes for

The goal is catching the **P1 class** — runtime crashes, broken deploys/migrations, and security-boundary regressions — not driving any external review bot to zero findings. Many low-severity bot comments (a duplicated constant, a mutable default that already has a guard, an unnecessary formatter-skip comment) are low value, and bots produce false positives and retract findings too. Spend the review's attention on what would actually break in production; don't pad the report to look thorough.

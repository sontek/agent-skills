---
name: review-pr
description: Review a pull request or branch by fanning out to specialized review sub-agents (code review, security, Django access/perf, GitHub Actions), then coalescing their findings into concise, human-toned suggested review comments for your approval. Use when asked to "review this PR", "do a full PR review", "give me review comments", "run all the reviewers", or "multi-agent review" — when you want consolidated comments to post, not fixes applied. Never posts comments or edits code without explicit approval. For a single-aspect pass use review-code or review-security; to auto-apply fixes use auto-review-code; to fix CI/feedback use iterate-pr.
allowed-tools: Read, Grep, Glob, Bash, Task
---

# Review PR

Fan out to the specialized review agents, coalesce their findings, and turn them into the review comments a thoughtful human reviewer would leave on the PR. You **propose** comments; the user approves before anything is posted. You do not edit code and you do not post without explicit go-ahead.

This differs from siblings: `review-code`/`review-security` run one agent and return findings verbatim; `auto-review-code` loops and auto-applies fixes; `iterate-pr` fixes CI. This skill consolidates *multiple* reviewers into postable comments for approval.

## Process

### 1. Resolve scope

- **Local branch (default):** base branch is `main` unless overridden (`git symbolic-ref refs/remotes/origin/HEAD`). Diff range `<base>...HEAD`. List files: `git diff --name-only <base>...HEAD`.
- **GitHub PR (`/review-pr 123` or a PR URL):** `gh pr view <n> --json number,headRefName,baseRefName,title,body`, then check out or diff that branch's range. Capture the PR title/body as grounding.

Stop and ask if scope is empty or ambiguous.

### 2. Pick reviewers from the diff

Always dispatch **`code-reviewer`** and **`security-auditor`**. Add specialists when the diff touches their domain:

| Signal in changed files | Add agent |
|---|---|
| Django code (`models.py`, `views.py`, `urls.py`, DRF, `from django`) | `django-access-reviewer`, `django-perf-reviewer` |
| `.github/workflows/*.yml` | `gha-security-reviewer` |

Don't run a specialist with nothing in scope — it wastes a round and adds noise.

### 3. Dispatch in parallel

Invoke every selected agent in a **single message with multiple Task calls** so they run concurrently. Use `subagent_type: agent-skills:<agent-name>`. Each prompt is self-contained (isolated context): pass the mode, base branch + diff range (or the path list), the PR title/body, any caller "don't flag X — intentional" notes verbatim, and a pointer to `REVIEW_GUIDELINES.md` if present. Tell each agent to follow its own rubric and output format.

### 4. Coalesce

Merge the raw findings into one deduplicated set:

- **Dedup / corroborate.** Same file within ±3 lines on the same root issue → one comment. Note when multiple reviewers flagged it — corroboration raises confidence and ordering.
- **Drop noise.** In branch mode, drop findings outside the diff. Drop pure style/formatting unless the user asked for it or it's egregious; batch genuine nits into one summary comment rather than many.
- **Order** by severity, then by file/line.
- **Don't re-review.** Trust each agent's call; your job is consolidation and phrasing, not a fourth opinion.

### 5. Turn findings into review comments

Rewrite each kept finding as a comment a human reviewer would actually leave: concise, specific, one point per comment, no priority-code jargon, no AI attribution. Label with a conventional tag (**blocking**, **suggestion**, **question**, **nit**, **praise**) and anchor to `file:line`. Add a ```suggestion block only when the exact replacement is unambiguous. See [references/comment-style.md](references/comment-style.md) for tone rules and worked before/after examples.

### 6. Present for approval — never post unprompted

Emit the consolidated comments as rendered markdown in chat, grouped by file, each with its anchor, tag, and text. Then ask the user which to post (e.g., "all", "1,3,5", "none", or edits). **Do not call `gh` to post until the user explicitly approves.** This is the core contract of the skill.

### 7. Post on approval (optional)

Only after the user picks comments, post them. Mechanics, batching, and the `gh`/GraphQL commands are in [references/posting.md](references/posting.md). Posted comments carry no AI-attribution markers (matching the repo's commit/PR convention). For a local-only branch with no PR, offer the comments as text or to open a PR first via `create-pr`.

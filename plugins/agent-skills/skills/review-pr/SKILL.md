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

**Read the existing discussion first.** Before dispatching reviewers, pull what's already been said so you don't re-litigate settled threads — this is the difference between a useful pass and noise on a PR that's been through three review rounds:

- Inline review comments + threads: `gh api repos/{owner}/{repo}/pulls/<n>/comments` (path, line, body, resolution where available).
- Top-level discussion: `gh pr view <n> --comments`.
- Recent commits on the branch (`git log --oneline <base>...HEAD`) — a later commit may have already addressed an earlier comment (e.g. a refactor that moved the flagged code). Skim the diffs of commits that look like they respond to feedback.

Keep this discussion as grounding for the coalesce step. For a local branch with no PR, there's no discussion to read — skip.

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

- **Dedup / corroborate.** Same file within ±3 lines on the same root issue → one comment. Note when multiple reviewers flagged it — but corroboration only counts when they reasoned independently. Findings that trace back to the same source you fed every agent (a bot comment, the PR body) are one hypothesis restated, not independent votes; don't let the repetition inflate confidence.
- **Verify every anchor — here, not at post time.** Sub-agent line numbers drift (they restate from memory or count off a stale buffer). Re-resolve each `file:line` against the current file and confirm the line both exists and falls inside a diff hunk (`git diff <base>...HEAD -- <path>`). A comment on a non-existent or out-of-diff line fails to post or lands in the wrong place. Re-anchor to the nearest relevant changed line; if you can't, demote it to a top-level comment.
- **Verify the claim, not just the location.** A sub-agent finding is a hypothesis, not a fact — agents assert consequences ("this leaks", "raises a ResourceWarning", "fails CI", "one user's data is served to another") that read plausibly from the diff but are often wrong in practice. Before stating one as fact, confirm it the way the author would challenge it: read the actual library/source for any behavioral claim instead of trusting recalled semantics; check the environment CI actually uses (a type/lint error in your venv can pass in an isolated pre-commit hook with different deps); run a minimal repro where the branch and deps make that feasible. For facts you can't see from code — is this data per-user, does this endpoint vary per tenant — ask the caller or phrase the comment as a question. Verify hardest what you'll assert most strongly; if you can't confirm it, demote it to a question or drop it. A confidently-asserted consequence that turns out false costs far more reviewer trust than a missed nit.
- **Separate introduced from pre-existing.** A finding on code this PR *moved or renamed but did not change* is not introduced here — common in refactors. Default those to an off-PR note or follow-up ticket, not a PR comment; if you do surface one, label it pre-existing and say it needn't block. Reserve PR comments for what the diff actually changed.
- **Cross-check against the existing discussion.** For each surviving finding, check whether it was already raised in the comments/threads you read in step 1. If it was discussed and resolved (author explained intent, deferred it, or a later commit fixed it), drop it — re-posting a settled thread is pure noise. If it was raised but left open, reference that rather than opening a parallel thread. Only carry forward findings that are genuinely new to the conversation.
- **Triage by value, not just severity.** Trust each agent to *surface* a candidate issue, but verify its technical claim (above) before stating it as fact; whether it earns the author's attention is your judgment, not theirs. Be willing to recommend dropping low-value findings outright — a weak comment spends reviewer trust. Drop findings outside the diff, and pure style/formatting unless asked or egregious; batch genuine nits into one summary comment.
- **Order** by value (severity × confidence × in-scope), then by file/line.

### 5. Turn findings into review comments

Rewrite each kept finding as a comment a human reviewer would actually leave: concise, specific, one point per comment, no priority-code jargon, no AI attribution. **No tag prefixes** (`blocking —`, `suggestion —`, etc.) — they read like a robot filled in a form. Convey weight in the prose itself: a must-fix reads as must-fix because the consequence is concrete and you say "before merge" in words; a minor point opens with "small one:"; a question just asks. Anchor each to `file:line`. Add a ```suggestion block only when the exact replacement is unambiguous. See [references/comment-style.md](references/comment-style.md) for the prose-weight guidance and worked before/after examples.

### 6. Present for approval — never post unprompted

Emit the consolidated comments as rendered markdown in chat, grouped by file, each with its anchor and text. Lead with the highest-value comments and say so — if the set is mostly low-value, state that up front and name which one or two actually matter, rather than presenting ten findings as equals. For each, tell the user in plain prose what you'd do with it — whether it's worth posting, worth dropping as not worth the noise, or better as an off-PR note/ticket than a line comment — and why, in a sentence. Don't stamp a `Recommendation:` label on it; just say it like you'd tell a colleague ("I'd post this one — it's the real tradeoff of the refactor", "I'd drop this, it's already settled in the thread"). The user shouldn't have to ask "are these worth posting?" — answer it before they do. Then ask which to post (e.g., "all", "1,3,5", "none", or edits). **Do not call `gh` to post until the user explicitly approves.** This is the core contract of the skill.

### 7. Post on approval (optional)

Only after the user picks comments, post them. Mechanics, batching, and the `gh`/GraphQL commands are in [references/posting.md](references/posting.md). Posted comments carry no AI-attribution markers (matching the repo's commit/PR convention). For a local-only branch with no PR, offer the comments as text or to open a PR first via `create-pr`.

---
name: review-pr
description: Review a pull request or branch by fanning out to specialized review sub-agents (code review, security, Django access/perf, GitHub Actions), then coalescing their findings into concise, human-toned suggested review comments for your approval. Use when asked to "review this PR", "do a full PR review", "give me review comments", "run all the reviewers", or "multi-agent review" — when you want consolidated comments to post, not fixes applied. Two modes: reviewing someone else's PR (default, proposes comments to post) and self-reviewing your own PR before you hand it off (`/review-pr self`, or "self-review my PR", "is my PR complete / merge-ready" — adds completeness and merge-readiness checks, output is a verdict for you). Propose-only in both modes: never edits code, never posts without approval. For a single-aspect pass use review-code or review-security; to auto-apply fixes use auto-review-code; to fix CI/feedback use iterate-pr.
allowed-tools: Read, Grep, Glob, Bash, Task
---

# Review PR

Fan out to the specialized review agents, coalesce their findings, and turn them into the review comments a thoughtful human reviewer would leave on the PR. You **propose** comments; the user approves before anything is posted. You do not edit code and you do not post without explicit go-ahead.

This differs from siblings: `review-code`/`review-security` run one agent and return findings verbatim; `auto-review-code` loops and auto-applies fixes; `iterate-pr` fixes CI. This skill consolidates *multiple* reviewers into postable comments for approval.

## Modes

- **Incoming review (default).** Reviewing someone else's PR or branch to leave feedback. Output is suggested comments for your approval to post. This is the rest of this document, steps 1–7.
- **Self-review (`self`).** Reviewing your *own* just-authored PR before handing it off, to catch the completeness and merge-readiness gaps a diff-only pass misses. Shares the fan-out and coalesce (steps 1–4) but adds orchestrator-level passes and produces a verdict for you instead of postable comments — see [Self-review mode](#self-review-mode-self) at the end. Triggered by `/review-pr self [123]`, by a self-review phrasing ("review my own PR", "is this complete / merge-ready"), or auto-detected when the PR author is you (`gh api user --jq .login` matches the PR author) or it's your current local branch with no open PR. When genuinely unsure, default to incoming review.

Both modes are **propose-only**: never edit code, never post or push without explicit approval. A review tells you what it found; you decide what to do with it.

## Process

### 1. Resolve scope

- **Local branch (default):** base branch is `main` unless overridden (`git symbolic-ref refs/remotes/origin/HEAD`). Diff range `<base>...HEAD`. List files: `git diff --name-only <base>...HEAD`.
- **GitHub PR (`/review-pr 123` or a PR URL):** `gh pr view <n> --json number,headRefName,baseRefName,title,body`, then check out or diff that branch's range. Capture the PR title/body as grounding.

**Read the existing discussion first.** Before dispatching reviewers, pull what's already been said so you don't re-litigate settled threads — this is the difference between a useful pass and noise on a PR that's been through three review rounds:

- Inline review comments + threads: `gh api repos/{owner}/{repo}/pulls/<n>/comments` (path, line, body, resolution where available).
- Top-level discussion: `gh pr view <n> --comments`.
- Recent commits on the branch (`git log --oneline <base>...HEAD`) — a later commit may have already addressed an earlier comment (e.g. a refactor that moved the flagged code). Skim the diffs of commits that look like they respond to feedback.
- Pending automated reviewers. `gh pr checks <n>` (or `gh pr view <n> --json statusCheckRollup`) for Greptile / CodeRabbit / Cursor Bugbot / Copilot. If one is still `IN_PROGRESS`, your pass is **preliminary** — say so in the final output and offer to reconcile once it posts; don't present a clean verdict while a bot review is mid-run, since it may surface exactly what you cleared. If a bot has already commented, read those comments as input — but treat each as *one hypothesis to verify* (it flows through `finding-verifier` like any finding), not as independent corroboration that inflates confidence (see the coalesce dedup rule).

Keep this discussion as grounding for the coalesce step. For a local branch with no PR, there's no discussion to read — skip.

Stop and ask if scope is empty or ambiguous.

### 2. Pick reviewers from the diff

Always dispatch **`code-reviewer`** and **`security-auditor`**. Add specialists when the diff touches their domain:

| Signal in changed files | Add agent |
|---|---|
| Django code (`models.py`, `views.py`, `urls.py`, DRF, `from django`) | `django-access-reviewer`, `django-perf-reviewer` |
| Application-tier code in any backend stack — Flask, FastAPI, Starlette, **Django views/services/tasks/workers**, Go `net/http` / gin / echo, Node express / fastify, plain Python services/workers | `perf-reviewer` |
| `.github/workflows/*.yml` | `gha-security-reviewer` |
| IaC (`*.tf`, `*.tofu`, `infra/`) | `iac-reviewer` |
| DB layer (migrations, raw SQL, `import sqlalchemy`/`sqlmodel`, `cursor.execute`/`text(`) | `sql-reviewer` |

Don't run a specialist with nothing in scope — it wastes a round and adds noise. `perf-reviewer` may co-fire with `django-perf-reviewer` or `sql-reviewer` (including on Django code) — dispatch both and let the coalesce dedup (step 4) collapse the overlap into corroboration; don't suppress one to avoid it.

### 3. Dispatch in parallel

Invoke every selected agent in a **single message with multiple Task calls** so they run concurrently. Use `subagent_type: sontek-skills:<agent-name>`. Each prompt is self-contained (isolated context): pass the mode, base branch + diff range (or the path list), the PR title/body, any caller "don't flag X — intentional" notes verbatim, and a pointer to `REVIEW_GUIDELINES.md` if present. Tell each agent to follow its own rubric and output format.

### 4. Coalesce

Merge the raw findings into one deduplicated set:

- **Dedup / corroborate.** Same file within ±3 lines on the same root issue → one comment. Note when multiple reviewers flagged it — but corroboration only counts when they reasoned independently. Findings that trace back to the same source you fed every agent (a bot comment, the PR body) are one hypothesis restated, not independent votes; don't let the repetition inflate confidence.
- **Verify every anchor — here, not at post time.** Sub-agent line numbers drift (they restate from memory or count off a stale buffer). Re-resolve each `file:line` against the current file and confirm the line both exists and falls inside a diff hunk (`git diff <base>...HEAD -- <path>`). A comment on a non-existent or out-of-diff line fails to post or lands in the wrong place. Re-anchor to the nearest relevant changed line; if you can't, demote it to a top-level comment.
- **Sweep for gaps before you verify.** The finders run in isolated context and each sees only its own angle, so a defect that falls *between* them — or one the diff re-exposes in an untouched line of a touched function — is the dominant miss. After dedup and anchor-verification, dispatch **one** fresh `code-reviewer` agent (`subagent_type: sontek-skills:code-reviewer`) as a recall gap-sweep: give it the diff scope **and the consolidated findings list so far**, and tell it to re-read the diff and enclosing functions looking ONLY for defects not already on the list — not to re-confirm what's there. Fold any genuinely new candidates in; they flow through `finding-verifier` and the value-triage below like every other finding, so the sweep buys recall without spending precision — a noisy candidate gets verified and triaged out before it ever reaches a comment. A clean sweep that finds nothing is the expected outcome on a tight diff; it must not pad to look thorough.
- **Verify the claim, not just the location — via `finding-verifier`.** A sub-agent finding is a hypothesis, not a fact; finders assert consequences ("this leaks", "raises a ResourceWarning", "fails CI", "one user's data is served to another") that read plausibly from the diff but are often wrong, and they self-validate in the same context that produced the finding. After dedup and anchor-verification, dispatch the **`finding-verifier`** agent (`subagent_type: sontek-skills:finding-verifier`) once on the surviving findings — pass each finding's fingerprint, claimed mechanism and consequence, and the diff scope, but **not** the finders' reasoning. It reads the actual library/source for behavioral claims instead of trusting recalled semantics, checks the environment CI really uses (a type/lint error in your venv can pass in an isolated pre-commit hook with different deps), runs a minimal repro where feasible, and returns CONFIRMED / PLAUSIBLE / REFUTED. **Drop REFUTED.** For a PLAUSIBLE finding whose `needs_confirmation` names a fact you can't see from code — is this data per-user, does this endpoint vary per tenant — ask the caller or phrase the comment as a question rather than asserting it. A confidently-asserted consequence that turns out false costs far more reviewer trust than a missed nit, so the verifier checks hardest what you'd assert most strongly. **A finding that *contradicts* an existing thread is the highest-priority candidate to verify, not an exception to it.** When a sub-agent dismisses a bot or human finding as wrong, or asserts the opposite of what a thread concluded, that disagreement is the signal to run the *original* claim through `finding-verifier` (and to trace it yourself) — never to post the sub-agent's rebuttal on its say-so. You are about to tell the author "the other reviewer is wrong," and that needs stronger evidence than an ordinary finding, because being wrong there burns trust twice: once for the bad comment, once for overruling a correct one.
- **Separate introduced from pre-existing.** A finding on code this PR *moved or renamed but did not change* is not introduced here — common in refactors. Default those to an off-PR note or follow-up ticket, not a PR comment; if you do surface one, label it pre-existing and say it needn't block. Reserve PR comments for what the diff actually changed.
- **Count what you claim, against the diff.** Any quantified or scoped assertion a comment will make — "adds 40s", "four call sites", "every test", "this is the only file without the guard" — gets checked against the actual diff before it reaches prose, not at post time. Confirm both the number and the introduced-vs-pre-existing split: "this PR added four slow tests" is wrong if two of them are pre-existing and only the sleep they share is what the diff touched. Correct the figure or cut it; never carry an unverified magnitude into a comment.
- **Cross-check against the existing discussion.** For each surviving finding, check whether it was already raised in the comments/threads you read in step 1. If it was discussed and resolved (author explained intent, deferred it, or a later commit fixed it), drop it — re-posting a settled thread is pure noise. If it was raised but left open, reference that rather than opening a parallel thread. Only carry forward findings that are genuinely new to the conversation.
- **Triage by value, not just severity.** Trust each agent to *surface* a candidate issue, but verify its technical claim (above) before stating it as fact; whether it earns the author's attention is your judgment, not theirs. Be willing to recommend dropping low-value findings outright — a weak comment spends reviewer trust. Drop findings outside the diff, and pure style/formatting unless asked or egregious; batch genuine nits into one summary comment.
- **Order** by value (severity × confidence × in-scope), then by file/line.

### 5. Turn findings into review comments

Rewrite each kept finding as a comment a human reviewer would actually leave: concise, specific, one point per comment, no priority-code jargon, no AI attribution. **No tag prefixes** (`blocking —`, `suggestion —`, etc.) — they read like a robot filled in a form. Convey weight in the prose itself: a must-fix reads as must-fix because the consequence is concrete and you say "before merge" in words; a minor point opens with "small one:"; a question just asks. Anchor each to `file:line`. Add a ```suggestion block only when the exact replacement is unambiguous. See [references/comment-style.md](references/comment-style.md) for the prose-weight guidance and worked before/after examples.

Before presenting, run the composed comment text through `review-tone`'s hygiene — `comment-style.md` is the PR-comment layer on top of review-tone, so the shared "reads human" rules apply here too. At minimum run the mechanical em-dash strip (`python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/strip_emdashes.py`) and rewrite any flagged sentence so it flows without the dash, leaving code and `suggestion` blocks untouched. Confirm zero em-dashes, en-dashes, or `--` remain in the prose.

### 6. Present for approval — never post unprompted

Emit the consolidated comments as rendered markdown in chat, grouped by file, each with its anchor and text. Lead with the highest-value comments and say so — if the set is mostly low-value, state that up front and name which one or two actually matter, rather than presenting ten findings as equals. For each, tell the user in plain prose what you'd do with it — whether it's worth posting, worth dropping as not worth the noise, or better as an off-PR note/ticket than a line comment — and why, in a sentence. Don't stamp a `Recommendation:` label on it; just say it like you'd tell a colleague ("I'd post this one — it's the real tradeoff of the refactor", "I'd drop this, it's already settled in the thread"). The user shouldn't have to ask "are these worth posting?" — answer it before they do. Then ask which to post (e.g., "all", "1,3,5", "none", or edits). **Do not call `gh` to post until the user explicitly approves.** This is the core contract of the skill.

### 7. Post on approval (optional)

Only after the user picks comments, post them. Mechanics, batching, and the `gh`/GraphQL commands are in [references/posting.md](references/posting.md). Posted comments carry no AI-attribution markers (matching the repo's commit/PR convention). For a local-only branch with no PR, offer the comments as text or to open a PR first via `create-pr`.

## Self-review mode (`self`)

When the PR under review is your *own* (see [Modes](#modes)), the question changes. Incoming review asks "what comments would I leave"; self-review asks **"is my fix complete, and is this PR merge-ready, before I hand it off."** Run the normal fan-out and coalesce (steps 1–4) for correctness — the reviewers and `finding-verifier` work identically — then add the orchestrator-level passes below. They catch the omissions a per-finding, diff-only review structurally misses.

- **Plan-vs-execution drift.** Reread the plan you wrote at the start of this task (the "what I'll do / keep / move" list). Diff it against the actual change: everything you said you'd KEEP still present, everything you'd MOVE in its new home with no facts lost in transit, everything you'd ADD in the diff, everything you'd REMOVE gone. For prose edits (SKILL.md, docs, tool descriptions), list the discrete facts in the old text vs the new — any fact in old-not-new must appear elsewhere or be justified as obsolete. Plan drift is the most common bug in refactors and is invisible to the per-finding reviewers, who never saw your plan.
- **Breadth — did I fix every instance?** Identify the predicate your fix targets (a specific call shape, error path, filter), grep the whole repo for it, and for each hit *not* in your diff ask whether the same bug lives there. Unlike incoming review (which stays inside the diff and is careful about pre-existing code), self-review is allowed and expected to cross into pre-existing sites — fixing your bug everywhere is part of the fix. For every matching site: include it, or name it explicitly as a deliberate follow-up. "I'll do it later" is fine; silent omission is not. Name every site you considered and chose to skip.
- **Mergeability.** Diff-clean is not merge-ready. Run `gh pr view <n> --json mergeable,mergeStateStatus,statusCheckRollup`. `mergeable` must be `MERGEABLE` (`CONFLICTING` needs a rebase on the base branch). The rollup should be non-empty with no `FAILURE`; an empty rollup when CI is configured means CI never fired (conflicts blocked it, or a token-opened PR suppressed it) — diagnose why. Don't call a PR ready while checks are `IN_PROGRESS`. This pass only *reports* the state; fixing the failures is `iterate-pr`'s job.
- **PR hygiene** (when a PR exists). Every template `[ ]` checkbox checked or marked `[ ] N/A (reason)`; every `(describe…)` placeholder filled; a conventional-commit *title* (a `--fill` title can be a branch slug even when the commit body is fine — check the title separately); `Fixes #n` present if it closes an issue. No AI-attribution footer (per our convention — this is where we diverge from tools that add a "generated by" receipt).

The metadata-staleness, sibling-test-coverage, and sibling-pattern-uplift checks are not listed here because the `code-reviewer` agent already runs them in the fan-out — they surface as ordinary findings and flow into "Completeness gaps" below.

**Output is a verdict for you, not comments to post.** Lead with what's wrong — honest self-review: a test gap is a gap, not "acceptable"; a missed call site is a gap, not "out of scope." If you ran the breadth check and found nothing, say so; silence on an expected step reads as a skipped step. Structure:

- **Plan drift** — items that didn't land as planned, or "none."
- **Completeness gaps** — breadth misses, missing sibling tests, stale surface metadata, missing follow-up notes, or "none."
- **Bugs** — from the reviewer fan-out, already verified by `finding-verifier`.
- **Mergeability** — quote the `mergeable` / `mergeStateStatus` / CI values; don't paraphrase.
- **PR hygiene.**
- **Verdict** — one of: "clean, ready to merge" (only if every section above is empty and `mergeable` is `MERGEABLE` with required checks green); "fix before merge: <list>"; or "land as-is, follow-up needed: <list>."

**Self-review is still propose-only.** List the high-confidence fixups you'd make, but do not apply them and do not push — surface the verdict and let the user decide, exactly as incoming review proposes comments without posting. To actually apply the fixups, hand off to `auto-review-code`; to drive CI green, `iterate-pr`.

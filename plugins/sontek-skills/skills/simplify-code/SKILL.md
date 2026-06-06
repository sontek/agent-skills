---
name: simplify-code
description: Review changed code for AI-generated slop and apply fixes. Use when the user says "simplify", "clean this up", "deslop", "tidy up", or after AI-generated code lands. Fans out to focused code-quality lane detectives (comments, structure, typing, complexity, defensive), coalesces their findings, and applies the safe ones.
allowed-tools: Read, Grep, Glob, Bash, Task
---

# Simplify Code

A deslop pipeline that always **fans out** to focused lane detectives in isolated
context, coalesces their findings, and applies the safe ones. This is the
quality/maintainability sibling to `review-code` (which owns correctness, security,
and performance) — run it independently when you want to deslop without a bug
review.

Each lane runs the `code-simplifier` agent against a **subset** of the AI-slop
rubric, so each instance reasons deeply about one cohesive family instead of
spreading thin across the whole rubric. The skill resolves scope, selects lanes,
dispatches them read-only, then coalesces and applies. Use this instead of the
built-in `/simplify`, which spawns generic agents without the curated rubric.

## When to invoke

- "Simplify this", "clean this up", "deslop", "tidy up", after AI-generated code lands
- Pre-PR cleanup of a feature branch
- "Run simplify-code on the codebase" — a deeper, repo-wide cut (see `codebase` mode)

Don't use for: finding bugs / security / perf issues (use `review-code`); looping
review+simplify until clean (use `auto-review-code`, which calls this fan-out).

## Modes

Pick one before invoking; default `branch` when there's a diff, else `paths`.

- **`branch` (default)** — changed files vs the main branch (`git diff --name-only <base>...HEAD`).
- **`paths`** — an explicit file/dir list from the caller, reviewed as-is. Do not default to whole-repo; ask if missing.
- **`codebase`** — a deliberate repo-wide cut. Do **not** read every file: **hotspot-rank** first (largest files, highest churn via `git log --format= --name-only | sort | uniq -c | sort -rn | head`, and most-recently-changed), take the top slice, and budget each lane to that slice. Always `log()` what was ranked-in and what was left out — a repo-wide pass that silently samples reads as "covered everything" when it didn't.

## Process

### 1. Resolve scope

- `branch`: base branch (default `main`; `git symbolic-ref refs/remotes/origin/HEAD` or an explicit override). Diff range `<base>...HEAD`; collect changed files. If the working tree is dirty with no branch diff, fall back to `git diff`/`git diff HEAD`, then to files edited this conversation.
- `paths`: the caller's explicit list.
- `codebase`: the hotspot-ranked slice (above).

Capture the explicit file list — lane detectives run in isolated context and see only what you pass.

### 2. Select lanes (domain-gating)

The pipeline always fans out, but a lane only spins up if the scope contains a
file it could match — running a lane with nothing in scope just adds noise (the
same lane-selection `review-code` does). A lane with no matching files is skipped,
not dispatched.

| Lane | Rule IDs it owns | Runs when scope has |
|---|---|---|
| **comments** | `comments.placeholder-comments`, `comments.template-comments`, `comments.docstring-rationale`, `comments.change-narration`, `comments.over-explanatory` | any source file (it carries the delete-vs-tighten gate, so all comment rules MUST stay in this one lane) |
| **structure** | `structure.duplicate-function-signatures`, `structure.pass-through-functions`, `structure.trivial-helper-method`, `structure.bandaid-special-case`, `structure.inline-data-blob`, `dead-code.unused-abstraction` | any source file (owns the cross-file + pre-existing-sibling pass) |
| **typing** | `typing.codebase-alias-missed`, `stdlib.reinvented` | a statically-typed / stdlib-rich language (Python, TS, Go, Rust, Java, C#…); skip for markup/config-only |
| **complexity** | `structure.reducible-complexity`, `organization.god-module`, `organization.barrel-file-density` | any source file (god-module/barrel benefit from ≥2 files, but reducible-complexity fires on one) |
| **defensive** | `defensive.error-swallowing`, `async.unnecessary-return-await`, `async.trivial-wrapper` | any source file with error handling or async constructs |

A docs-only or config-only diff may select **no** lanes — that's a valid outcome; say so and stop.

### 3. Ground the pass

- Note whether `CLAUDE.md` / `AGENTS.md` / `REVIEW_GUIDELINES.md` exist (lanes load them for project standards).
- Capture any caller "don't flag X, it's intentional" notes **verbatim** to forward to every lane. A caller note removes a comment from the *delete* bucket only — it does NOT exempt it from `comments.over-explanatory` tightening.

### 4. Dispatch the lanes in parallel

Invoke every selected lane in a **single message with multiple Task calls** so they run concurrently. Each uses `subagent_type: sontek-skills:code-simplifier`. Each prompt is self-contained (isolated context) and must say:

- **Lane focus:** "Run the **`<lane>`** lane only. From your rubric, apply **exactly** these rule IDs: `[<ids>]`. Report findings for these rules only; ignore every other rule."
- **Read-only:** "Return your normal per-file findings report (rule IDs + evidence + precise before → after). **Do NOT edit any files** — this skill applies the fixes."
- **Scope:** the mode, the diff range or explicit file list, and the changed-file list.
- **Grounding:** pointer to `CLAUDE.md`/`AGENTS.md`/`REVIEW_GUIDELINES.md` if present; the caller "don't flag X" notes verbatim.
- **Lane-specific:**
  - **structure** — "Run the cross-file Phase-0 fingerprint pass over the full scope, AND compare each new/changed function against pre-existing siblings in its package (same dir, sibling subclasses of a shared base)." Pass the full file list.
  - **typing** — "Run the Phase-0b calibration (inversion protocol) and emit the candidates-considered ledger before findings."

### 5. Coalesce, verify, and apply

- **Dedup across lanes.** Lanes own disjoint rule IDs, but the same line can surface in two (e.g. an inline-data blob inside an over-complex function). Same file within ±3 lines on the same root issue → one entry; note the corroboration.
- **Comment gate already resolved.** The delete-vs-tighten arbitration lives entirely inside the comments lane (that's why the comment rules are one lane), so there's no cross-lane comment conflict to referee here.
- **Verify the risky ones (optional but preferred).** For any structural fix where you can't prove behavior is preserved, dispatch the `finding-verifier` agent on the consolidated list before applying — drop REFUTED, keep CONFIRMED/PLAUSIBLE.
- **Apply per `auto-review-code`'s apply policy** (don't re-implement it — that skill owns the triage rules):
  - **Auto-apply low-risk, behavior-preserving fixes** where existing tests are the regression guard: slop comments, `comments.docstring-rationale`/`change-narration`/`template-comments` deletions, `comments.over-explanatory` tightening, trivial wrappers, defensive `try/catch` with no semantic loss, test-only helper inlines.
  - **Always flag (never auto-apply) the higher-risk rules**, matching their own rubric notes: `structure.reducible-complexity`, `organization.god-module`, `structure.bandaid-special-case` (structural refactors), `dead-code.unused-abstraction` (deletes code + its tests), and anything inlining a production-called helper or changing a public signature/type. State the precise before → after and call sites; let the user decide.
  - **Dismiss false positives** with a one-line rationale (lanes over-flag by design; pruning is the skill's job).

Report what each lane found, what was applied, and what was flagged, in one short summary — no per-finding narration during the pass.

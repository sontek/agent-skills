---
name: review-with-hunk
description: Collaborate with the user over a live Hunk diff-review session — read the inline notes they leave on hunks and act on them, and/or walk them through a changeset by steering their view and annotating it. Use when the user has Hunk open and says "address my hunk notes", "I left comments in Hunk", "I commented on the diff", "fix what I flagged", "walk me through this diff", "explain these changes in Hunk", or wants a back-and-forth conversation about a diff they're viewing. Two moves in one loop — `address` (you -> agent: act on the user's `--type user` notes) and `walk` (agent -> user: navigate + leave explanatory comments). Distinct from `review-code` (multi-agent review of your own branch, no live session), `review-pr` (comments on someone else's GitHub PR), `auto-review-code` (applies a review's findings with no human in the loop), and the tool's bundled `hunk-review` skill (documents only the agent-narrates direction and misses the user's notes by default).
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# Review With Hunk

Drive a **live Hunk review session** in conversation with the user. Hunk is an
interactive terminal diff viewer; the user keeps the TUI open and you reach into their
session over the local daemon with `hunk session *` commands. This skill owns the
collaboration loop over that session — nothing else. It does not run code review
heuristics (`review-code`), post GitHub comments (`review-pr`), or apply findings
headless (`auto-review-code`).

The loop has two moves, and which one you make is driven by what the user just said:

- **address** — the user left notes on hunks; read them and make the changes.
- **walk** — the user wants a guided tour; steer their view and annotate it.

A real session usually interleaves them: walk a diff, the user annotates from the tour,
you address, they push back, repeat. Stay in the loop until the user is done.

## Critical: the user owns the session, not you

- **Never run `hunk diff`, `hunk show`, `hunk stash show`, or any interactive `hunk`
  command.** The TUI is the user's. You only ever use `hunk session *` subcommands
  against the daemon.
- If there is **no live session**, stop and ask the user to open Hunk on the diff they
  want to review (e.g. `hunk diff` in their terminal). You cannot create one for them.
- When you `navigate` or `comment add`, you are mutating the user's *live* view in real
  time — their cursor jumps, your note appears. Treat their screen with care.

## Resolve the session first (every time)

```bash
hunk session list --json
```

Take the `sessionId` from the result and target every later command by that ID.

- **Do not rely on `--repo .`.** The daemon records the repo root as the path *it* sees,
  which can differ from the path *your* shell sees (sandbox/worktree path remaps are
  common). `--repo .` then fails with "No active session matches repoRoot ...". The
  `sessionId` is unambiguous; prefer it.
- If `session list` returns nothing but the user says Hunk is open, localhost may be
  blocked by the agent sandbox — retry with network/sandbox escalation before concluding
  there's no session.
- If multiple sessions match a repo, the `sessionId` disambiguates.

## The two comment buckets (the thing the bundled skill gets wrong)

A session holds two independent sets of annotations, and the **default `comment list`
shows the wrong one for this workflow**:

| Bucket | `source` | id prefix | How to list | Author |
|--------|----------|-----------|-------------|--------|
| **Review notes** | `user` | `user:` | `comment list <id> --type user` | the human |
| **Live comments** | `agent`/`ai` | `mcp:` | `comment list <id>` (default) or `--type agent\|ai\|live` | you |

`--type all` returns both. **To find the user's feedback you MUST pass `--type user`
(or `--type all`).** Bare `comment list` shows only the agent bucket — an agent that
runs it sees no user notes and wrongly concludes there's nothing to do. This is the
single most important rule in this skill.

Each note (JSON via `--json`) carries: `noteId`, `source`, `filePath`, `hunkIndex`
(0-based), `newRange`/`oldRange` (1-based line numbers), `body`, `author`, `createdAt`,
`editable`. Anchor your work to `filePath` + `newRange`/`oldRange` — those are
unambiguous. (`hunkIndex` in JSON is 0-based, but `navigate --hunk` and the TUI display
are 1-based; add 1 if you navigate by hunk number read from JSON.)

## Move: address (you -> agent)

The user left notes; turn them into changes.

1. **Read them:** `hunk session comment list <id> --type user --json`.
2. For each note, in a sensible order:
   - Read the note `body` and the code at `filePath:newRange`. If you need the diff
     context, `hunk session review <id> --json` (add `--include-patch` only for files
     you must see in raw form).
   - Make the change with `Edit`/`Write`. Match surrounding style. Keep it scoped to
     what the note asked — don't fold in unrelated cleanups.
   - **Leave a done-marker:** add an `[agent]` comment on the same line summarizing what
     you did, and **leave the user's note in place** so they can verify and clear it
     themselves:
     ```bash
     hunk session comment add <id> --file <path> --new-line <n> \
       --author agent \
       --summary "Addressed: <what changed>. Verify, then clear your note."
     ```
   - Do **not** `comment rm` the user's note. Auto-removing it destroys the feedback if
     you misread the intent and leaves the user no signal to check. The done-marker +
     their original note is the verification trail.
3. If a note is ambiguous or you disagree, don't guess — leave an `[agent]` comment
   asking for clarification (or ask in chat) and skip the edit until resolved.
4. After the batch, report a short summary (see Final summary) and re-list `--type user`
   in case the user added notes while you worked.

For several notes you already understand, batch the done-markers with one stdin call:

```bash
printf '%s' '{"comments":[{"filePath":"a.py","newLine":12,"summary":"Addressed: ..."}]}' \
  | hunk session comment apply <id> --stdin
```

## Move: walk (agent -> user)

The user wants a guided tour of a changeset (often one you just authored).

1. **Learn the shape without bloating context:** `hunk session review <id> --json`. Pull
   raw diff text with `--include-patch` only for the files you actually need to read.
2. **Pick a narrative order** — start where the change's story begins, not file order.
3. For each hunk worth stopping at: `hunk session navigate <id> --file <path> --hunk <n>`
   (the user's view jumps there), then leave one `[agent]` comment. Flavors:
   - **Orientation** — what this file/hunk is and why it matters.
   - **Rationale** — why the change was made.
   - **Risk flag** — "this is the critical part; scrutinize X."
   - **Explicit ask** — "Verify: confirm Y is the behavior you want?" The user answers in
     chat or by dropping a `user` note on that hunk (which you then `address`).
4. **Don't annotate every hunk.** Highlight what the user wouldn't spot themselves and
   where you're uncertain. Use `--focus` on the one note that should actively steer them.
5. Summarize when done and hand the floor back — the user will annotate or reply.

Step between annotated hunks with `hunk session navigate <id> --next-comment` /
`--prev-comment`.

## Conventions

- **ASCII only in comment bodies.** No UTF-8 arrows (`->` not the unicode arrow), no
  unicode check marks. The user reviews these inline and wants plain ASCII.
- **Quote `--summary` / `--rationale` defensively** in the shell.
- **Mark authorship:** pass `--author agent` on every comment you add, so the buckets
  stay clean and the user can tell your notes from theirs at a glance.
- **Don't `comment clear`** unless the user explicitly asks — it wipes their notes too.
- **Reload to change what's under review:** `hunk session reload <id> -- diff [ref]
  [-- <paths>]` (always include `--` before the nested command). Use this if the user
  asks to look at a different ref/range; never open a new TUI.

## Exit conditions

- **Addressed** — every actionable user note has a code change and an `[agent]`
  done-marker; ambiguous ones have a clarifying comment. User notes left intact for the
  user to verify and clear.
- **Walked** — the notable hunks are annotated in a coherent order; asks are explicit;
  summary delivered. Floor handed back to the user.
- **No session** — Hunk isn't open; asked the user to launch it. Do not proceed.
- **Blocked** — a note needs a product/intent decision you can't make; surfaced the
  specific question and paused on that note.

## Final summary (emit to user)

```markdown
## Hunk session: <one-line of what happened>

**Addressed (N notes):**
- `file:line` — <note> -> <what you changed>  [done-marker left]
**Needs your input:**
- `file:line` — <the ambiguity / question>
**Walked (M hunks):** <one line on the tour, if you walked>

Your notes are left in place — verify the done-markers, then clear them in Hunk
(`hunk session comment rm <id> <note-id>`). I re-read `--type user` after each round, so
just leave new notes and tell me to continue.
```

## Common errors

- **"No active session matches repoRoot ..."** — you used `--repo .` across a path remap.
  Resolve via `hunk session list --json` and target by `sessionId`.
- **"No active Hunk sessions"** — Hunk isn't open (ask the user) or localhost is sandbox-
  blocked (retry with escalation).
- **Bare `comment list` shows nothing** — that's the agent bucket. Add `--type user`.
- **"No visible diff file matches ..."** — the file isn't in the loaded review; check
  `hunk session review <id>`, and `reload` if the user wants different content.
- **"Specify exactly one navigation target"** — pick one of `--hunk`, `--new-line`, or
  `--old-line`.
- **"Pass the replacement Hunk command after `--`"** — `reload` needs `--` before the
  nested `diff`/`show`.

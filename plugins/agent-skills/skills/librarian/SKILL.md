---
name: librarian
description: Cache and refresh remote git repositories under `~/.cache/checkouts/<host>/<org>/<repo>` so future references reuse a local copy instead of re-cloning. Use when the user references a remote git repository — full URL (`https://github.com/foo/bar`, `git@github.com:foo/bar.git`), `owner/repo` shorthand, or asks Claude to "look at", "read", "search", or "find something in" an external repo by name. Returns a stable local path that downstream skills (review-code, grep, Read) can use directly.
---

# Librarian

Resolve a remote git repository to a stable local cache path under `~/.cache/checkouts/<host>/<org>/<repo>`. Future references to the same repo reuse the cache (with a throttled fetch + fast-forward) instead of cloning again.

## When to use

- User points at a remote repo by URL, `owner/repo` shorthand, or `git@...`.
- You need to read, grep, or analyze code in a repo that isn't already cloned locally.
- A previous session referenced the same repo and you want the same path.

## Quick start

```bash
bash plugins/agent-skills/skills/librarian/checkout.sh <repo> --path-only
```

The script prints the local checkout path on stdout. Examples:

```bash
bash checkout.sh mitsuhiko/minijinja --path-only
bash checkout.sh github.com/mitsuhiko/minijinja --path-only
bash checkout.sh https://github.com/mitsuhiko/minijinja --path-only
bash checkout.sh git@github.com:mitsuhiko/minijinja.git --path-only
```

All resolve to the same path: `~/.cache/checkouts/github.com/mitsuhiko/minijinja`.

## What the script does

1. Parses the repo reference into `host/org/repo`.
2. Clones if missing (uses `--filter=blob:none` for a partial clone — fast and small).
3. Reuses the existing checkout if present.
4. Throttles `git fetch` to once every 300 seconds by default.
5. Attempts a fast-forward merge if the working tree is clean and an upstream is configured.

`owner/repo` defaults to `github.com`. Override with `LIBRARIAN_DEFAULT_HOST` if you need a different host.

## Force a fresh fetch

When correctness depends on the latest upstream (e.g., reviewing a PR that just landed), bypass the throttle:

```bash
bash checkout.sh <repo> --force-update --path-only
```

## Don't edit inside the cache

The cache is shared across sessions. Editing a file in `~/.cache/checkouts/...` leaks state to future invocations. If you need to modify a checked-out repo:

- Copy the relevant files out of the cache, or
- Create a separate worktree (`git worktree add ...`) and edit there.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `LIBRARIAN_CACHE_ROOT` | `~/.cache/checkouts` | Override cache root |
| `LIBRARIAN_DEFAULT_HOST` | `github.com` | Host for `owner/repo` shorthand |
| `LIBRARIAN_UPDATE_INTERVAL` | `300` | Fetch throttle in seconds |

## Workflow

1. Resolve the repo path with `checkout.sh --path-only`.
2. Use that path for subsequent `Read`, `Grep`, `Glob`, or `find` operations.
3. On later references, call `checkout.sh` again — it will reuse and (if stale) refresh.

## Adapted from

- [mitsuhiko/agent-stuff](https://github.com/mitsuhiko/agent-stuff/tree/main/skills/librarian)

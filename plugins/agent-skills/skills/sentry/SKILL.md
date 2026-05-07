---
name: sentry
description: Fetch and analyze Sentry data — issues (grouped errors), events (individual occurrences with stack traces and breadcrumbs), transactions, and logs. Use when the user asks to "look at Sentry", "fetch this Sentry issue", "find errors in Sentry", "search Sentry events", "what happened in Sentry around <time>", "get the latest event for issue X", or wants Claude to investigate a production error using Sentry data. Authenticates via `~/.sentryclirc`. Composes with review-code / iterate-pr (e.g., debug a Sentry issue, then produce a fix PR).
---

# Sentry

Pull Sentry data for debugging via the Sentry API. Auth comes from `~/.sentryclirc`.

## Auth setup

Scripts read the auth token from `~/.sentryclirc`. If the file is missing or the token is missing/stale:

```bash
sentry-cli login
```

Or write the file by hand:

```ini
[auth]
token=sntryu_<your-token>
```

Tokens come from `https://sentry.io/settings/account/api/auth-tokens/` — needs at least `event:read`, `project:read`, `org:read`.

## Quick reference

| Goal | Command |
|---|---|
| Find errors in a time window | `search-events.js --org X --start 2026-05-07T15:00:00 --level error` |
| List unresolved issues | `list-issues.js --org X --status unresolved` |
| Get full issue with latest stack trace | `fetch-issue.js <issue-id-or-url> --latest` |
| Get full event with breadcrumbs | `fetch-event.js <event-id> --org X --project Y --breadcrumbs` |
| Search logs | `search-logs.js --org X "level:error"` |

All scripts live under `./scripts/` relative to this skill folder.

## Common workflows

### "What went wrong at this time?"

```bash
# All events in a 2-hour window
./scripts/search-events.js --org myorg --project backend \
    --start 2026-05-07T15:00:00 --end 2026-05-07T17:00:00

# Just errors in that window
./scripts/search-events.js --org myorg --start 2026-05-07T15:00:00 --level error

# A specific transaction
./scripts/search-events.js --org myorg --start 2026-05-07T15:00:00 \
    --transaction process-incoming-email
```

### "What's broken in production right now?"

```bash
# Unresolved errors in the last 24h
./scripts/list-issues.js --org myorg --status unresolved --level error --period 24h

# High-frequency issues (most events)
./scripts/list-issues.js --org myorg --query "times_seen:>50" --sort freq

# Issues affecting users
./scripts/list-issues.js --org myorg --query "is:unresolved has:user" --sort user
```

### "Drill into a specific issue or event"

```bash
# Issue with the latest event (stack trace, breadcrumbs)
./scripts/fetch-issue.js 5765604106 --latest
./scripts/fetch-issue.js https://sentry.io/organizations/myorg/issues/123/ --latest
./scripts/fetch-issue.js MYPROJ-123 --org myorg --latest

# Specific event with all breadcrumbs
./scripts/fetch-event.js abc123def456 --org myorg --project backend --breadcrumbs
```

### "Find by tag"

```bash
# Custom tag (thread_id, request_id, user_id)
./scripts/search-events.js --org myorg --tag thread_id:th_abc123

# By user email
./scripts/search-events.js --org myorg --query "user.email:*@example.com"

# By trace ID (links errors that share a request)
./scripts/search-events.js --org myorg --query "trace:abc123def456"
```

## Script reference

### `fetch-issue.js <issue-id-or-url> [options]`

Get a grouped issue. Accepts numeric ID, full URL, or short ID like `MYPROJ-123` (with `--org`).

| Flag | Purpose |
|---|---|
| `--latest` | Include latest event with full stack trace |
| `--org <org>` | Required for short IDs |
| `--json` | Raw JSON output |

### `fetch-event.js <event-id> --org <org> --project <project> [options]`

Full details of a single event.

| Flag | Purpose |
|---|---|
| `--breadcrumbs, -b` | All breadcrumbs (default: last 30) |
| `--spans` | Span tree for transactions |
| `--json` | Raw JSON |

### `search-events.js [options]`

Search via Sentry Discover.

Time range:
- `--period 24h` / `7d` / `14d` (relative)
- `--start <ISO>` / `--end <ISO>` (absolute)

Filters:
- `--org`, `--project`
- `--query <discover-query>` (raw Discover syntax)
- `--transaction <name>` (filter by transaction name)
- `--tag <key:value>` (repeatable)
- `--level error|warning|info`
- `--limit <n>` (default 25, max 100)
- `--fields <a,b,c>` (which fields to include)

Discover query examples:
```
transaction:process-*           wildcard match
level:error                     level filter
user.email:foo@bar.com          user filter
environment:production          environment
has:stack.filename              has stack trace
```

### `list-issues.js [options]`

List grouped issues.

| Flag | Purpose |
|---|---|
| `--org`, `--project` | Project scope (`--project` repeatable) |
| `--query <q>` | Issue search query |
| `--status unresolved\|resolved\|ignored` | Status filter |
| `--level error\|warning\|info\|fatal` | Level filter |
| `--period 14d` | Time period (default 14d) |
| `--limit <n>` | Max results (default 25) |
| `--sort date\|new\|priority\|freq\|user` | Sort order |

Issue query examples:
```
is:unresolved
is:assigned / assigned:me
firstSeen:+7d / lastSeen:-24h
times_seen:>100
has:user
error.handled:0                 unhandled only
```

### `search-logs.js [query|url] [options]`

Search Sentry's Logs Explorer.

| Flag | Purpose |
|---|---|
| `--org` | Required unless a Sentry URL is passed |
| `--project` | Filter by project |
| `--period 24h` | Time period (default 24h) |
| `--limit <n>` | Max results (default 100, max 1000) |

Log query examples:
```
level:error
message:*timeout*
trace:abc123
project:my-project
```

Also accepts a Sentry Logs Explorer URL directly:
```bash
./scripts/search-logs.js "https://myorg.sentry.io/explore/logs/?project=123&statsPeriod=7d"
```

## Debugging tips

1. **Start broad, then narrow.** Use `search-events.js` with a time range first; drill into specific events with `fetch-event.js`.
2. **Breadcrumbs are gold.** `fetch-event.js --breadcrumbs` shows the chain of actions before an error. Often the actual cause is 3-5 breadcrumbs back.
3. **Sort by frequency.** `list-issues.js --sort freq` surfaces the issues that actually matter at scale.
4. **Trace ID links cross-service errors.** If a downstream API failure surfaces in two services, both events share a `trace` tag. Search by it.
5. **Custom tags > tribal knowledge.** If your codebase tags events with `request_id`, `thread_id`, `tenant_id`, use them. They're the only way to correlate without trace context.

## Adapted from

- [mitsuhiko/agent-stuff](https://github.com/mitsuhiko/agent-stuff/tree/main/skills/sentry)

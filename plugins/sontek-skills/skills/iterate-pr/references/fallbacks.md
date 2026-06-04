# When scripts fail

The bundled scripts in [scripts.md](scripts.md) are a convenience — the workflow still works without them. If a script fails, fall back to `gh` CLI directly rather than aborting.

## `uv` not installed

Install `uv` (https://docs.astral.sh/uv/getting-started/installation/) or fall back to raw `gh` commands:

- Check status: `gh pr checks --json name,state,bucket,link`
- Failed logs: `gh run list --branch $(git branch --show-current) --limit 5 --json databaseId,name,status,conclusion` then `gh run view <run-id> --log-failed`
- Review threads: `gh api repos/{owner}/{repo}/pulls/{pr}/comments` and `gh api repos/{owner}/{repo}/issues/{pr}/comments`

When using `gh` directly, categorize feedback manually — look for `h:`/`m:`/`l:` markers and words like "must fix", "blocker", "nit", "style".

## Script runtime errors

Network blips, GitHub API rate limits, or transient auth hiccups will surface as non-zero exits. Retry once after a short delay. If the second attempt fails, fall back to raw `gh` commands above rather than looping.

## Parsing errors

If a script returns malformed JSON or unexpected output, emit the raw output to the user unprocessed — do not silently continue with an empty/default value. Treat parsing errors as a signal to switch to the `gh` CLI fallback.

---
name: create-pr
description: ALWAYS use this skill when creating or updating pull requests — never create or edit a PR directly without it. Follows conventional PR title format, respects repo PR templates when present, and produces concise descriptions focused on what and why. Trigger on any create PR, open PR, submit PR, make PR, update PR title, update PR description, edit PR, push and create PR, or prepare changes for review task.
---

# Create PR

Create pull requests following consistent conventions.

**Requires**: GitHub CLI (`gh`) authenticated and available.

## Prerequisites

Before creating a PR, ensure all changes are committed. If there are uncommitted changes, invoke the `commit` skill first to commit them properly.

```bash
git status --porcelain
```

If the output shows uncommitted changes that should be included, invoke the `commit` skill before proceeding.

## Process

### Step 1: Verify Branch State

```bash
# Detect the default branch — note the output for use in subsequent commands
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

```bash
# Check current branch and status (substitute the detected branch name above for BASE)
git status
git log BASE..HEAD --oneline
```

Ensure:
- All changes are committed
- Branch is up to date with remote
- Changes are rebased on the base branch if needed

### Step 2: Analyze Changes

Review what will be included in the PR:

```bash
# See all commits that will be in the PR (substitute detected branch name for BASE)
git log BASE..HEAD

# See the full diff
git diff BASE...HEAD
```

Understand the scope and purpose of all changes before writing the description.

### Step 3: Detect and Respect the Repo PR Template

Check for a repository PR template:

```bash
# Common template locations
ls -1 .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null
ls -1 .github/pull_request_template.md 2>/dev/null
ls -1 .github/PULL_REQUEST_TEMPLATE/*.md 2>/dev/null
```

**If a template is present:**
- Fill in the template's fields (checklist items, required sections) as applicable.
- Add why/context information in whatever section the template permits (e.g., "Description", "Motivation", or a free-form area).
- Do NOT discard or bypass the template — the repo owners put it there for a reason (team conventions, compliance requirements).

**If no template is present:** Use the default structure in Step 4.

### Step 4: Write the PR Description

When there's no repo template, use this structure:

```markdown
<brief description of what the PR does>

<why these changes are being made - the motivation>

<alternative approaches considered, if any>

<any additional context reviewers need>
```

**The PR description is read BEFORE the diff, not in addition to it.** A reviewer should be able to skim it in 30 seconds and know what they're about to review and why. Specifics live in the code; the description sets the context they need to read the code well.

**Do NOT include:**
- Checkbox lists of testing steps (unless the template requires them)
- **Diff-level details** — anything a reviewer will see by opening the Files tab:
  - File paths or filenames (e.g., `src/api/auth.py`)
  - Function, class, variable, or constant names (e.g., `_filter_config`, `DEFAULT_CONFIG`)
  - Line numbers
  - Test counts ("8 new tests"), test file paths, or individual test names
  - Itemized restatements of changes that mirror the diff structure ("renamed X, added Y, moved Z")
  - Implementation play-by-play ("rewrite the prompt in 7 places", "pipe X into Y")
- Customer data — customer/org names, user emails, support ticket contents, or PII. Describe the technical symptom, not who hit it. Reference the internal ticket (e.g. `Fixes ENG-1234`). Many PRs are visible on public repos.

It's fine to name the *subject* of the change when that's the clearest framing ("deprecate the old auth middleware") — the rule is don't duplicate the diff, not never name an identifier.

**Do include:**
- Clear explanation of what and why
- Links to relevant issues or tickets
- Context that isn't obvious from the code
- Notes on specific areas that need careful review

### Step 5: Create the PR

```bash
gh pr create --draft --title "<type>(<scope>): <description>" --body "$(cat <<'EOF'
<description body here>
EOF
)"
```

**Title format** follows commit conventions:
- `feat(scope): Add new feature`
- `fix(scope): Fix the bug`
- `ref: Refactor something`

## PR Description Examples

### What "summary, not diff" looks like

❌ **Too verbose — duplicates the diff:**

> Adds `SUPPORTED_INFERENCE_KEYS` capability map and `_filter_inference_config`
> in `src/stacklet/jun0/bedrock.py` so `_start_converse_stream` strips any
> `inferenceConfig` keys the chosen model rejects. Flips two inline
> `inference_config={"temperature": 0}` callers (`_auto_execute_and_summarize`,
> `_summarize_results`) to use `DEFAULT_INFERENCE_CONFIG`. Adds 8 new unit tests
> in `tests/unit/jun0/test_bedrock.py` parametrized over opus/sonnet/haiku/unknown.

✅ **Right scope — what changed and why:**

> Filter unsupported `inferenceConfig` keys per model family before each Bedrock
> call. Fixes jun0 crashing with `temperature is deprecated` on every non-router
> LLM call when deployed against Opus.
>
> Picked an explicit per-model capability map over retry-on-error: behavior is
> deterministic and testable, and future per-model quirks are a one-row update.

### Feature PR

```markdown
Add Slack thread replies for alert notifications

When an alert is updated or resolved, we now post a reply to the original
Slack thread instead of creating a new message. This keeps related
notifications grouped and reduces channel noise.

Previously considered posting edits to the original message, but threading
better preserves the timeline of events and works when the original message
is older than Slack's edit window.

Refs ENG-1234
```

### Bug Fix PR

```markdown
Handle null response in user API endpoint

The user endpoint could return null for soft-deleted accounts, causing
dashboard crashes when accessing user properties. This adds a null check
and returns a proper 404 response.

Found while investigating ENG-5678.

Fixes ENG-5678
```

### Refactor PR

```markdown
Extract validation logic to shared module

Moves duplicate validation code from the alerts, issues, and projects
endpoints into a shared validator class. No behavior change.

This prepares for adding new validation rules in ENG-9999 without
duplicating logic across endpoints.
```

## Issue References

Reference issues in the PR body:

| Syntax | Effect |
|--------|--------|
| `Fixes #1234` | Closes GitHub issue on merge |
| `Fixes ENG-1234` | Closes Jira/Linear ticket |
| `Refs GH-1234` | Links without closing |
| `Refs LINEAR-ABC-123` | Links Linear issue |

## Guidelines

- **One PR per feature/fix** — Don't bundle unrelated changes
- **Keep PRs reviewable** — Smaller PRs get faster, better reviews
- **Explain the why** — Code shows what; description explains why
- **Mark WIP early** — Use draft PRs (`--draft`) for early feedback

## Editing Existing PRs

If you need to update a PR after creation, use `gh api` instead of `gh pr edit`:

```bash
# Update PR description
gh api -X PATCH repos/{owner}/{repo}/pulls/PR_NUMBER -f body="$(cat <<'EOF'
Updated description here
EOF
)"

# Update PR title
gh api -X PATCH repos/{owner}/{repo}/pulls/PR_NUMBER -f title='new: Title here'

# Update both
gh api -X PATCH repos/{owner}/{repo}/pulls/PR_NUMBER \
  -f title='new: Title' \
  -f body='New description'
```

Note: `gh pr edit` is currently broken due to GitHub's Projects (classic) deprecation.

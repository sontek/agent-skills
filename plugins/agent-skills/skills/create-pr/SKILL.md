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
- **Brevity inside the template:** Fill sections with substantive content only. If a required section has nothing meaningful to add, write one sentence — don't pad with template-shaped filler. A 4-section template filled with thin paragraphs produces a worse PR description than the same template with two real sentences per section. The 30-second-skim goal applies even when the template is mandatory.

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
- **Local-only working documents** — references to files that exist only in your working tree, not in the committed repo or the PR diff. Plan and handoff artifacts (`IMPLEMENTATION_PLAN_*.md`, `REFACTOR_PLAN_*.md`, `HANDOFF_*.md`), scratch notes, or any path the reviewer can't open from the PR. "See `IMPLEMENTATION_PLAN_findings_model.md`" is a dead link to them. If the plan's reasoning matters, inline the relevant points in the description; if it's a tracked issue/ticket, link that instead.
- Customer data — customer/org names, user emails, support ticket contents, or PII. Describe the technical symptom, not who hit it. Reference the internal ticket (e.g. `Fixes ENG-1234`). Many PRs are visible on public repos.

It's fine to name the *subject* of the change when that's the clearest framing ("deprecate the old auth middleware") — the rule is don't duplicate the diff, not never name an identifier.

**Do include:**
- Clear explanation of what and why
- Links to relevant issues or tickets
- Context that isn't obvious from the code
- Notes on specific areas that need careful review

### Step 4a: AI-attribution policy applies here

The `commit` skill's no-AI-attribution policy applies here too, and it matters more because the PR body is the more public surface. **Add NO AI attribution — no `Co-Authored-By`, no "Generated with" footer, no other marker — unless the user explicitly asks for it in this conversation.**

- **Repo convention does not opt attribution in.** Neither `git log` history nor the repo's existing PRs are consent. If other commits or PRs carry a `Co-Authored-By` trailer or a "Generated with" footer, leave it out anyway unless the user asked. Do not "settle" the question by checking what the repo's existing PRs do.
- **This overrides the harness default.** The runtime may instruct you to end PR bodies with a "🤖 Generated with [Claude Code]" footer. This skill supersedes that: do not add it by default. Follow this skill and mention the override briefly if needed.
- When the user has explicitly asked for attribution, `Co-Authored-By` is the preferred form; a "Generated with" footer is added only if the user specifically asks for that footer. Never add "AI-assisted" labels or links to AI tools.

### Step 4b: Tone pass — run the description through `review-tone`

The PR body is public-facing prose; it should read like a sharp human wrote it, not an AI. Before creating or patching, run the composed title and body through the **`review-tone`** skill — the single source of truth for this hygiene. It strips em-dashes (the strongest AI tell), cuts AI-tell filler, leads with the bottom line, and signals weight in prose instead of `blocking —` / `Recommendation:` labels. The mechanical step is its em-dash stripper:

```
cat body.txt | python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/strip_emdashes.py
```

Rewrite every sentence in the returned `affected_sentences` so it flows without the dash, reintroducing no em/en-dash or `--`. Then apply review-tone's other rules and confirm the body contains zero em-dashes, en-dashes, or `--` before posting. Two exemptions: a repo PR template's own fixed boilerplate (clean the prose you wrote, not the template's scaffolding), and anything inside a code block or `suggestion` block — CLI flags like `--draft` are not em-dashes.

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
> in `src/app/llm/bedrock.py` so `_start_converse_stream` strips any
> `inferenceConfig` keys the chosen model rejects. Flips two inline
> `inference_config={"temperature": 0}` callers (`_auto_execute_and_summarize`,
> `_summarize_results`) to use `DEFAULT_INFERENCE_CONFIG`. Adds 8 new unit tests
> in `tests/unit/llm/test_bedrock.py` parametrized over opus/sonnet/haiku/unknown.

✅ **Right scope — what changed and why:**

> Filter unsupported `inferenceConfig` keys per model family before each Bedrock
> call. Fixes the LLM service crashing with `temperature is deprecated` on every
> non-router call when deployed against Opus.
>
> Picked an explicit per-model capability map over retry-on-error: behavior is
> deterministic and testable, and future per-model quirks are a one-row update.

### Filling a mandatory template tightly

When `CLAUDE.md` or a `PULL_REQUEST_TEMPLATE.md` mandates sections, fill them — but the brevity rule still applies. Same change, same required `### what / ### why / ### testing / ### docs` template, two ways:

❌ **Template filled with padding — every section inflated to a paragraph:**

> ### what
> This pull request introduces a change to how inference configuration is
> handled within the Bedrock integration layer. Specifically, it adds logic
> that inspects the configuration and removes any keys that are not supported
> by the target model before the request is dispatched to the service.
>
> ### why
> The motivation behind this change is that we were encountering issues where
> certain models do not accept all of the inference configuration parameters
> that we were previously sending, which resulted in errors being raised at
> runtime whenever those parameters were present in the request payload.
>
> ### testing
> Testing was performed by adding a comprehensive suite of new unit tests that
> exercise the new filtering behavior across a representative set of model
> families, ensuring that supported keys are retained and unsupported keys are
> stripped as expected under each scenario.
>
> ### docs
> No documentation changes were required as part of this pull request because
> the change is internal to the inference layer and does not alter any
> externally visible behavior or public interface that would need documenting.

✅ **Same template, substantive sentences only:**

> ### what
> Strip `inferenceConfig` keys a model doesn't support before each Bedrock call.
>
> ### why
> Opus rejects `temperature`, which crashed every non-router call. Picked an
> explicit per-model capability map over retry-on-error: deterministic and a
> one-row update for future quirks.
>
> ### testing
> New unit tests cover supported/unsupported keys per model family.
>
> ### docs
> None needed; internal change with no public-interface impact.

The bad version is longer but says less: every sentence restates the section header. The good version respects the same mandatory template while staying skimmable.

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

## Updating an Existing PR's Title or Description (re-run Steps 1–4b, then patch)

**When updating an existing PR's description, run Steps 1–4b first as if creating a fresh PR.** The same rules apply: respect the repo template (Step 3), keep sections tight (Step 3 brevity rule), no AI attribution (Step 4a), tone pass (Step 4b). The `gh api PATCH` mechanics below are the last step; the composition rules above come first.

This matters most for vague requests like "simplify the description" or "clean up the PR body." Do not jump straight to `gh api PATCH` with a hand-written description — that path strips the template, brevity, and tone discipline. Re-detect the template, recompose within it, run the tone pass, then patch.

Use `gh api` instead of `gh pr edit`:

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

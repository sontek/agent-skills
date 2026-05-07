---
name: update-changelog
description: Update `CHANGELOG.md` (or `CHANGELOG`) with notable user-facing changes since the last release tag. Use when the user asks to "update the changelog", "update CHANGELOG.md", "write release notes", "prepare release notes", or "add unreleased entries". Adds entries to the `## Unreleased` section, preserves existing format, and filters out trivial commits (typo fixes, internal refactors, dependency bumps without security impact).
---

# Update Changelog

Add notable user-facing changes since the last release tag to the changelog's `## Unreleased` section.

## Workflow

### 1. Determine baseline version

```bash
git describe --tags --abbrev=0
```

If there are no tags, **stop and ask the user** for an explicit baseline (commit SHA, branch, or "since first commit"). Defaulting to "since first commit" produces unwieldy changelogs and almost never matches user intent.

### 2. Read commits since baseline

```bash
git log <baseline>..HEAD --oneline
git log <baseline>..HEAD          # for full messages when needed
```

When PRs landed via squash-merge, the PR number is usually in the subject line (e.g., `feat: add zip filter (#841)`). Capture it for the changelog entry.

### 3. Locate the changelog file

Prefer `CHANGELOG.md`. Fall back to `CHANGELOG` (no extension) if `.md` doesn't exist. Read the existing file to understand its format before writing.

### 4. Filter for notable changes

**Include** changes that affect users:
- New features
- Bug fixes that change observable behavior
- Breaking changes
- Performance improvements users will notice
- Security fixes (always)
- Deprecations and removals

**Exclude** changes that don't:
- Internal refactors with no behavior change
- Test additions / fixes
- CI / build tweaks
- Doc-only changes (unless documentation is the product)
- Dependency bumps (unless they bring user-facing changes or fix vulnerabilities)
- Typo fixes in code or comments

### 5. Write entries to the Unreleased section

Add to the existing `## Unreleased` (or `## [Unreleased]`, matching the file's style). If no `Unreleased` section exists, add one at the top in the same style as existing version headings.

If `## Unreleased` already has content, **append** to it; do not replace.

## Format conventions

- Use the existing file's bullet style (`*` or `-`) — match what's there.
- Order entries within a version: breaking changes → features → fixes → other.
- Reference PRs as `#NUMBER`. Don't include raw commit SHAs.
- Use past tense or imperative — match the file's style.
- Wrap code references in backticks (`` `module.function` ``).

## Examples

**Good entries**
- `Added support for free-threading Python. #841`
- `Fixed a regression where empty arrays raised on `|sort` filter. #823`
- `Improved error reporting when task claim expires.`
- `Breaking: removed the deprecated `fooLegacy` option (use `foo` instead).`

**Bad entries**
- `Fixed bug` (too vague)
- `Updated dependencies` (insignificant unless a CVE is fixed)
- `Refactored internal helpers` (internal change)
- `Fixed typo in comment` (trivial)

## Sample output

```markdown
## Unreleased

* Added multi-key support to the `|sort` filter. #827
* Fix `not undefined` with strict undefined behavior. #838
* Added support for free threading Python. #841

## 2.12.0

* Item or attribute lookup will no longer swallow all errors in Python. #814
* Added `|zip` filter. #818
```

## Notes

- Preserve the existing changelog's heading style, bullet style, and spacing.
- If the project has a non-default branch (`develop`, `next`, etc.), treat that as "current" instead of `main`.
- When in doubt about whether a change is significant, err on the side of including it.
- Don't tag a release as part of this skill — that's a separate workflow.

## Adapted from

- [mitsuhiko/agent-stuff](https://github.com/mitsuhiko/agent-stuff/tree/main/skills/update-changelog)

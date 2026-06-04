---
name: create-branch
description: Create git branches following naming conventions. Use when creating new feature branches, bug fix branches, or any branch for development work. Defines the branch naming standards used across commit and PR skills.
argument-hint: '[optional description of the work]'
---

# Create Branch

Create git branches following consistent naming conventions.
Keep this workflow non-interactive unless the user explicitly asks to choose the name manually.

## Branch Naming Convention

Branch names follow `<type>/<short-description>` (kebab-case, ASCII, ideally 3-6 words).

### Branch Types

| Type | Use when |
|------|----------|
| `feat` | New functionality |
| `fix` | Broken behavior now works |
| `ref` | Behavior stays the same, structure changes |
| `perf` | Same behavior, faster |
| `chore` | Maintenance of existing tooling/config |
| `style` | Visual or formatting only |
| `docs` | Documentation only |
| `test` | Tests only |
| `ci` | CI/CD config |
| `build` | Build system or dependencies |
| `meta` | Repo metadata |
| `license` | License changes |

When unsure: use `feat` for new things, `ref` for restructuring, `chore` for maintenance.

## Workflow

1. **Resolve the work description:**
   - If `$ARGUMENTS` is present, use it
   - Otherwise inspect local state:
     ```bash
     git diff
     git diff --cached
     git status --short
     ```
   - If there are local changes, derive a short description from the diff
   - If there are no local changes, use a generic description like `repo-maintenance`, `tooling-update`, or `work-in-progress`

2. **Classify the branch type** from the table above based on the work being done.

3. **Generate the branch name** as `<type>/<short-description>`. Keep `<short-description>` kebab-case, ASCII-only, ideally 3-6 words.

4. **Choose the base without prompting:**
   ```bash
   git branch --show-current
   git remote | grep -qx origin && echo origin || git remote | head -1
   git symbolic-ref refs/remotes/<remote>/HEAD 2>/dev/null | sed 's|refs/remotes/<remote>/||' | tr -d '[:space:]'
   ```
   - If default branch detection fails, fall back to `main`, then `master`, then the current branch
   - If on a detached HEAD, branch from the current commit
   - If already on a non-default branch, branch from the current branch
   - Only switch to the default branch when the user explicitly asks

5. **Avoid collisions** by appending `-2`, `-3`, etc. until the name is unused locally and remotely.

6. **Create the branch:**
   ```bash
   git checkout -b <branch-name>
   ```
   Report the final branch name; do not stop for confirmation.

## Good Branch Names

```
feat/add-user-auth              # Clear, concise, descriptive
fix/null-pointer-dashboard      # Specific about what's being fixed
ref/extract-validation-logic    # Clear refactoring goal
test/add-api-tests              # Clear testing scope
```

## Common Mistakes to Avoid

| Mistake         | Bad Example                                   | Good Example       |
| --------------- | --------------------------------------------- | ------------------ |
| Too long        | `feature/add-authentication-system-for-users` | `feat/add-user-auth` |
| Too vague       | `fix-bug`                                     | `fix/null-pointer` |
| Wrong case      | `Feat/AddAuth`                                | `feat/add-auth`    |
| Personal prefix | `john/my-work`                                | `feat/feature-name` |
| Wrong separator | `feat_add_auth`                               | `feat/add-auth`    |
| No type         | `add-authentication`                          | `feat/add-auth`    |
| Spelled-out type | `feature/add-auth`                           | `feat/add-auth`    |

## Handling Uncommitted Changes

If there are uncommitted changes when you start:
- If they belong on the new branch, that's fine — `git checkout -b` carries them over
- If they belong elsewhere, stash first: `git stash`, create the branch, unstash on the correct branch

## Related Skills

- **commit skill**: Uses branch naming to verify commits aren't on main/master
- **create-pr skill**: Uses branch type to derive PR title prefix

---
name: review-code
description: Perform code reviews with prioritized, actionable findings. Use when reviewing pull requests, examining code changes, or providing feedback on code quality. Supports two modes — `branch` (default, reviews diff vs. main) and `paths` (reviews an explicit file/dir list as-is, ignoring git history). Covers correctness, performance, security, design, testing, and cross-cutting concerns.
---

# Review Code

You are acting as a code reviewer. Your job is to flag issues that matter, skip issues that don't, and produce output the author can act on immediately.

## Modes

Pick one before starting. If the invoker didn't specify, default to `branch`.

- **`branch` (default)** — Review the current branch's changes vs. the main branch. Only flag issues introduced by the diff; don't flag pre-existing code that wasn't touched. Include the Human Reviewer Callouts section in output.
- **`paths`** — Review the current state of an explicit list of files or directories, regardless of git history. Flag any issue in the reviewed code. Omit the Human Reviewer Callouts section entirely (there's no "change" to call out). Requires an explicit path list from the invoker — do not default to whole-repo.

The rules below apply to both modes unless noted.

## Change discipline (for your review)

- In `branch` mode: stay in the scope of the diff. Don't flag pre-existing code that wasn't touched.
- In `paths` mode: stay in the scope of the provided paths. Don't wander into files that weren't listed.
- Don't propose sweeping refactors. Don't demand rigor inconsistent with the rest of the codebase.
- Phrase findings as discrete, actionable items — not general critiques.

## Load project guidelines if present

Walk upward from the current working directory until you find a `REVIEW_GUIDELINES.md` file (check `.claude/REVIEW_GUIDELINES.md` first, then `REVIEW_GUIDELINES.md` at repo root). If found, its contents override the defaults below.

## Investigation approach

Before flagging anything:

1. List 5-7 plausible issues from the diff.
2. Gather evidence for each (check call sites, related tests, types).
3. Narrow to 1-2 most likely *real* issues per category.
4. Validate — read the code, don't speculate.
5. Only then write findings.

This prevents guess-and-check review cycles. Don't stop at the first plausible issue per category — the obvious one is often not the real one.

## What to flag

Flag issues that:

1. Meaningfully impact **correctness, performance, security, or maintainability**.
2. Are discrete and actionable (not general issues or bundled).
3. Don't demand rigor inconsistent with the rest of the codebase.
4. In `branch` mode: were introduced in the changes being reviewed (not pre-existing bugs). In `paths` mode: exist in the reviewed code, regardless of when they were introduced.
5. The author would likely fix if aware of them.
6. Don't rely on unstated assumptions about the codebase or author's intent.
7. Have provable impact on other parts of the code — identify the affected parts; don't just speculate.
8. Are clearly not intentional changes by the author.
9. Handle untrusted user input carefully — see the rules below.
10. Treat silent local error recovery (parsing/IO/network fallbacks) as high-signal candidates unless there's explicit boundary-level justification.

## Review checklist (by category)

### Correctness

- Potential exceptions, null/undefined access, out-of-bounds access
- Off-by-one errors, wrong operator, inverted conditions
- Race conditions, shared-state hazards, missed awaits
- Backwards compatibility — breaking API changes without migration path

### Performance

- Unbounded O(n²) operations, N+1 queries, unnecessary allocations
- Complex ORM queries with unexpected execution plans
- Loops triggering network/IO per iteration
- Unbounded memory growth or missing pagination

### Security

- Injection (SQL, command, LDAP, template), XSS, SSRF
- Access control gaps, IDOR (verify queries are scoped to the current user/tenant)
- Secrets or credentials in code, logs, or PR text
- Insecure deserialization, weak crypto, hardcoded keys

### Untrusted user input (strict)

1. Open redirects must validate against a trusted-domain allow-list (watch `?next_page=...`).
2. Always flag non-parametrized SQL.
3. For user-supplied URLs: HTTP fetches must protect against local-resource access (intercept DNS resolver, block private IP ranges).
4. Prefer **escape** over **sanitize** where possible (e.g., HTML escaping).

### Design

- Does the change fit existing architecture?
- Are component interactions logical?
- Are abstractions justified by current use, not speculative future use?
- Does it introduce a wrapper/abstraction without clear value?

### Testing

- Business logic covered by functional tests
- Component interactions covered by integration tests
- Critical user paths covered by end-to-end tests
- Tests assert on observable behavior, not implementation details
- No excessive branching/looping inside test bodies

### Code quality

- Naming conveys intent
- Comments explain *why* (non-obvious constraints), not *what* (obvious from code)
- Error messages reference stable identifiers, not mutable text

### Side effects

- Any change that affects other components, callers, or stored data
- Any migration, index change, or destructive operation

## Fail-fast error handling (strict)

When reviewing new or modified error handling, default to fail-fast. Evaluate every new or changed `try/catch`:

1. Identify what can fail and *why* local handling is correct at that exact layer.
2. Prefer **propagation** over local recovery. If the current scope can't fully recover while preserving correctness, rethrow (optionally with added context) instead of returning fallbacks.
3. Flag catch blocks that hide failure signals: returning `null`/`[]`/`false`, swallowing JSON parse failures, logging-and-continue, "best effort" silent recovery.
4. JSON parsing/decoding should fail loudly by default. Quiet fallback parsing is only acceptable with an explicit compatibility requirement and tested behavior.
5. Boundary handlers (HTTP routes, CLI entrypoints, supervisors) may translate errors, but must not pretend success or silently degrade.
6. If a catch exists only to satisfy lint/style without real handling, treat it as a bug.
7. When uncertain, prefer crashing fast over silent degradation.

## Priority levels

Tag each finding with a priority:

- **[P0]** — Drop everything to fix. Blocking. Universal (doesn't depend on input assumptions).
- **[P1]** — Urgent. Should be addressed in the next cycle.
- **[P2]** — Normal. Fix eventually.
- **[P3]** — Low. Nice to have.

## Finding comment style

- State *why* it's a problem.
- Communicate severity honestly — don't exaggerate.
- At most one paragraph.
- Keep code snippets under 3 lines.
- Use ` ```suggestion ` blocks ONLY for concrete replacement code. Preserve exact leading whitespace.
- Matter-of-fact tone — helpful, not accusatory.
- No flattery ("great job...") or filler.

## Approval policy

- Approve when only minor issues remain.
- Don't block on stylistic preferences.
- The goal is risk reduction, not perfect code.

## Long-term impact (flag for senior review)

Changes that need senior review attention:

- Database schema modifications
- API contract changes
- New framework or library adoption
- Performance-critical code paths
- Security-sensitive functionality

## Output format

```markdown
## Review

**Verdict:** `correct` (no blocking issues) | `needs attention` (has blocking issues)

### Findings

#### [P1] Brief title
- **Location:** `path/to/file.ext:line`
- **Issue:** Why this matters (1 paragraph).
- **Fix:** Short suggestion or `suggestion` block.

#### [P2] Brief title
...

### Human Reviewer Callouts (Non-Blocking) — `branch` mode only

Omit this entire section in `paths` mode. In `branch` mode, include only applicable callouts; omit the section entirely if none apply:

- **This change adds a database migration:** <files/details>
- **This change introduces a new dependency:** <package(s)/details>
- **This change changes a dependency (or the lockfile):** <files/package(s)/details>
- **This change modifies auth/permission behavior:** <what changed and where>
- **This change introduces backwards-incompatible public schema/API/contract changes:** <what changed and where>
- **This change includes irreversible or destructive operations:** <operation and scope>
- **This change adds or removes feature flags:** <feature flags changed>
- **This change changes configuration defaults:** <config var changed>
```

Rules for the Callouts section:

1. Only emit in `branch` mode — skip entirely in `paths` mode.
2. Informational for the human reviewer, not fix items.
3. Do not include them as Findings unless there's an independent defect.
4. These callouts alone must not change the verdict.
5. Only include callouts that apply to the reviewed change.
6. Keep each emitted callout bold exactly as written.
7. If none apply, omit the section header entirely.

## Common patterns to flag

### Python/Django — N+1 query

```python
# Bad
for user in users:
    print(user.profile.name)  # query per user

# Good
users = User.objects.prefetch_related('profile')
```

### TypeScript/React — missing effect dependency

```typescript
// Bad
useEffect(() => {
  fetchData(userId);
}, []);  // userId not in deps

// Good
useEffect(() => {
  fetchData(userId);
}, [userId]);
```

### Security — SQL injection

```python
# Bad
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
```

### Silent error swallowing (flag by default)

```javascript
// Bad — swallows the error
try {
  return JSON.parse(data);
} catch {
  return {};
}

// Good — fail loudly, or translate at an explicit boundary
return JSON.parse(data);  // let it throw
```

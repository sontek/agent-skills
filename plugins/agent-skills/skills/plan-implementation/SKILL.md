---
name: plan-implementation
description: Create structured implementation plans for NEW features, complex additions, or multi-phase work. Use when user asks to "create a plan" or "make an implementation plan" or work requires multiple distinct phases. Outputs a local IMPLEMENTATION_PLAN_<feature-name>.md file with phases, tasks, quality gates (code review, tests, linter, type checker), and status tracking. For restructuring existing code without changing behavior, use plan-refactor instead. If Claude Code is in plan mode, plan mode itself already produces an in-conversation plan via ExitPlanMode — use review-plan on that draft instead of invoking this skill.
---

# Implementation Plan

Create structured implementation plans for complex features, refactoring, or
multi-phase work. Use markdown files with phases and checklists to track
progress and ensure quality gates are met.

## When to Create an Implementation Plan

Create a plan when:

- Feature requires multiple distinct phases or steps
- Refactoring affects multiple files or systems
- Work will span multiple commits or PRs
- Task requires coordination across different areas
- Breaking down complex work helps clarify approach
- Need to track progress on long-running work

**Don't create a plan for:**

- Simple bug fixes
- Single-file changes
- Trivial updates
- Well-understood, straightforward tasks

## Plan Structure

Implementation plans use a markdown file named
`IMPLEMENTATION_PLAN_<feature-name>.md` in the repository root. Use a short,
descriptive feature name in kebab-case (lowercase with hyphens).

**Examples:**

- `IMPLEMENTATION_PLAN_user-authentication.md`
- `IMPLEMENTATION_PLAN_async-queue-processing.md`
- `IMPLEMENTATION_PLAN_api-v2-migration.md`

The plan includes:

1. **Overview** - Summary of what's being implemented and why
2. **Phases** - Ordered list of implementation phases with checklists
3. **Notes** - Additional context, decisions, or considerations

## Phase Template

Each phase follows this structure:

```markdown
## Phase N: [Phase Name]

**Goal:** [Clear statement of what this phase achieves]

**Status:** Not Started | In Progress | Complete

### Tasks

- [ ] [Specific task to complete]
- [ ] [Another task]
- [ ] [More tasks as needed]

### Quality Gates

- [ ] Code review (self-review changes before moving to next phase)
- [ ] Tests passing (run test suite and verify all tests pass)
- [ ] Linter passing (run linter and fix all issues)
- [ ] Type checker passing (run type checker and fix all issues)
- [ ] Manual testing (verify functionality works as expected)
```

**Phase Status Values:**

- **Not Started** - Phase hasn't been started yet
- **In Progress** - Currently working on this phase
- **Complete** - All tasks and quality gates are finished

## Creating the Plan

### 1. Understand the Requirements

Before creating the plan:

- Read all requirements and context
- Ask clarifying questions if needed
- Identify dependencies and constraints
- Consider architectural implications
- Review existing code patterns

### 2. Break Down Into Phases

Organize work into logical phases:

- **Each phase should be independently committable**
- **Phases should build on each other sequentially**
- **Each phase should have clear completion criteria**
- **Phases should be small enough to complete in one session**

Example phase breakdown for adding authentication:

1. Phase 1: Add database models and migrations
2. Phase 2: Implement authentication service
3. Phase 3: Add API endpoints
4. Phase 4: Add frontend integration
5. Phase 5: Add tests and documentation

### 3. Write the Plan File

Create `IMPLEMENTATION_PLAN_<feature-name>.md` in the repository root:

```markdown
# Implementation Plan: [Feature Name]

**Created:** [Date] **Status:** In Progress | Complete | Paused

## Overview

[2-4 sentence summary of what's being implemented and why. Include the problem
being solved and the high-level approach.]

## Phases

[Include each phase using the phase template above]

## Notes

### Decisions Made

- [Key architectural or implementation decisions]
- [Trade-offs considered]

### Open Questions

- [ ] [Any unresolved questions]
- [ ] [Items that need clarification]

### Dependencies

- [External dependencies or prerequisites]
- [Other features or systems this depends on]
```

### 4. Review the Plan

Before starting implementation:

- Verify phases are in logical order
- Ensure each phase has clear completion criteria
- Confirm quality gates are appropriate
- Check that all requirements are covered
- Offer to run the `review-plan` skill, which routes the plan through
  the `senior-engineer` (DRY, architecture, phase ordering) and, for
  user-facing work, the `product-manager` (scope, UX) agents. This is
  the cheapest point to catch architectural mistakes — before any code
  is written.

## Working With the Plan

### Starting a Phase

When beginning a phase:

1. Update phase status: `**Status:** In Progress`
2. Read through all tasks and quality gates
3. Ensure previous phases are complete
4. Create feature branch if needed

### During Implementation

As you work:

- Check off tasks as they're completed
- Add notes about unexpected issues or decisions
- Keep the plan current with actual implementation

### Completing a Phase

Before marking a phase complete:

1. Verify all tasks are checked off
2. Complete all quality gates:
   - [ ] Self-review code changes
   - [ ] Run tests: `pytest` or equivalent
   - [ ] Run linter: `ruff check .` or equivalent
   - [ ] Run type checker: `mypy .` or equivalent
   - [ ] Manually test the changes
3. Commit the phase changes
4. Mark phase as complete: `**Status:** Complete`
5. Commit the updated plan

### Updating the Plan

The plan is a living document:

- Add phases if you discover additional work
- Adjust phases if approach changes
- Add notes about important decisions or issues
- Update status regularly

## Example Plan

```markdown
# Implementation Plan: User Authentication

**Created:** 2026-01-07 **Status:** In Progress **Plan File:**
`IMPLEMENTATION_PLAN_user-authentication.md`

## Overview

Add JWT-based authentication to the API to secure endpoints and track user
actions. Currently all endpoints are public. This implements standard JWT
authentication with refresh tokens and role-based access control.

## Phases

### Phase 1: Database Models

**Goal:** Add user and authentication tables to database

**Status:** Complete

#### Tasks

- [x] Create User model with email, password_hash, role fields
- [x] Create RefreshToken model for token rotation
- [x] Generate and test database migrations
- [x] Add indexes on email and token fields

#### Quality Gates

- [x] Code review (self-review changes before moving to next phase)
- [x] Tests passing (run test suite and verify all tests pass)
- [x] Linter passing (run linter and fix all issues)
- [x] Type checker passing (run type checker and fix all issues)
- [x] Manual testing (verify migrations run successfully)

---

### Phase 2: Authentication Service

**Goal:** Implement core authentication logic and JWT handling

**Status:** In Progress

#### Tasks

- [x] Create AuthService class
- [x] Implement password hashing with bcrypt
- [x] Implement JWT token generation
- [x] Implement token refresh logic
- [ ] Add role-based permission checks
- [ ] Add rate limiting for login attempts

#### Quality Gates

- [ ] Code review (self-review changes before moving to next phase)
- [ ] Tests passing (run test suite and verify all tests pass)
- [ ] Linter passing (run linter and fix all issues)
- [ ] Type checker passing (run type checker and fix all issues)
- [ ] Manual testing (verify token generation and validation)

---

### Phase 3: API Endpoints

**Goal:** Add authentication endpoints to the API

**Status:** Not Started

#### Tasks

- [ ] Add POST /auth/register endpoint
- [ ] Add POST /auth/login endpoint
- [ ] Add POST /auth/refresh endpoint
- [ ] Add POST /auth/logout endpoint
- [ ] Add authentication middleware for protected routes
- [ ] Update existing endpoints to require authentication

#### Quality Gates

- [ ] Code review (self-review changes before moving to next phase)
- [ ] Tests passing (run test suite and verify all tests pass)
- [ ] Linter passing (run linter and fix all issues)
- [ ] Type checker passing (run type checker and fix all issues)
- [ ] Manual testing (test all endpoints with curl/Postman)

---

### Phase 4: Tests and Documentation

**Goal:** Add comprehensive tests and update documentation

**Status:** Not Started

#### Tasks

- [ ] Add unit tests for AuthService
- [ ] Add integration tests for auth endpoints
- [ ] Add tests for protected endpoint access
- [ ] Update API documentation
- [ ] Add authentication guide to README

#### Quality Gates

- [ ] Code review (self-review changes before moving to next phase)
- [ ] Tests passing (run test suite and verify all tests pass)
- [ ] Linter passing (run linter and fix all issues)
- [ ] Type checker passing (run type checker and fix all issues)
- [ ] Manual testing (verify docs are accurate and clear)

## Notes

### Decisions Made

- Using JWT instead of sessions for stateless authentication
- Using bcrypt for password hashing (industry standard)
- Implementing refresh tokens for better security
- Using role-based access control (admin, user roles)

### Open Questions

- [x] Should we support OAuth2 providers? - No, not in initial version
- [ ] What should token expiration time be? - Need to decide

### Dependencies

- Requires bcrypt library for password hashing
- Requires PyJWT library for JWT handling
- Database must support migrations
```

## Tips for Good Plans

**Keep phases small:**

- Each phase should be completable in 1-3 hours
- If a phase is too large, break it into multiple phases
- Smaller phases are easier to review and commit

**Be specific in tasks:**

- "Add User model" is better than "Database stuff"
- "Implement JWT token generation" is better than "Tokens"
- Clear tasks make progress tracking easier

**Update as you go:**

- Don't let the plan get stale
- Add phases if you discover more work
- Mark tasks complete as you finish them
- Add notes about important decisions

**Use quality gates consistently:**

- Always include the standard quality gates
- Add project-specific gates if needed (e.g., "Security review")
- Don't skip quality gates - they catch issues early

**Commit plan updates:**

- Commit the plan with the code changes for each phase
- This creates a history of progress
- Makes it easy to see what was done in each commit

## Tool Usage

When creating and working with plans:

- **Use Write tool** to create initial `IMPLEMENTATION_PLAN.md`
- **Use Edit tool** to update plan as work progresses
- **Use Read tool** to review current plan state
- **Use Bash tool** to run quality gate checks (tests, linter, type checker)
- **Use git commands** to commit plan updates with phase changes

## Integration with Other Skills

**Use with review-plan skill:**

- After writing the plan, offer `review-plan` for a senior-engineer /
  product-manager judgment pass before implementation starts.
- Apply any blocking findings by editing the plan file, then begin
  Phase 1.

**Use with commit skill:**

- Reference plan phases in commit messages:
  `feat(auth): Implement Phase 2 - Authentication service`
- Commit plan updates along with code changes

**Use with review-code skill:**

- Review each phase's changes before marking complete
- Quality gates include code review checkpoint

**Use with create-pr skill:**

- Can create PRs per phase for large features
- Or create single PR with all phases for smaller features
- Reference plan in PR description

## Common Mistakes

**Don't use generic filenames:**

- ❌ `IMPLEMENTATION_PLAN.md` (conflicts with other plans)
- ✅ `IMPLEMENTATION_PLAN_user-authentication.md` (unique and descriptive)

**Don't make phases too large:**

- ❌ Phase 1: Implement entire authentication system
- ✅ Phase 1: Add database models for authentication

**Don't skip quality gates:**

- ❌ Marking phase complete without running tests
- ✅ Run all quality gates before marking phase complete

**Don't let plan get stale:**

- ❌ Plan says "In Progress" on Phase 2, actually on Phase 4
- ✅ Update plan status as you complete each phase

**Don't be too vague:**

- ❌ Task: "Fix the thing"
- ✅ Task: "Add null check in getUserProfile function"

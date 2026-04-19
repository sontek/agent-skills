---
name: find-bugs
description:
  Find bugs, security vulnerabilities, and code quality issues in branch
  changes. Use when reviewing code for bugs, security issues, or quality
  problems. Thorough but concise reporting.
---

# Find Bugs and Security Issues

Review branch changes for bugs, security vulnerabilities, and code quality issues.

## Core Principles

- **Be thorough**: Check every file and every security category
- **Be accurate**: Don't report false positives or invent issues
- **Be concise**: Report real issues clearly without fluff
- **Prioritize**: Security > Bugs > Quality

## Change Discipline

- Write absolute minimum code required
- No sweeping changes
- No unrelated edits
- Stay focused on the specific task
- Don't break existing functionality without asking

## Investigation Approach

For each changed file:

1. Identify 5-7 potential vulnerability types that could apply
2. Narrow to 1-2 most likely based on:
   - User input points in the code
   - Data operations performed
   - Security controls present or absent
3. Verify with code inspection or existing tests
4. Only report confirmed, exploitable issues

This prevents false positives and focuses on real risks.

## Process

### Step 1: Get All Changes

```bash
# Get the full diff
git diff main...HEAD

# If truncated, list changed files
git diff main...HEAD --name-only

# Get all commits
git log main..HEAD --oneline
```

**Review every changed file completely:**
- If diff is truncated, read each file individually with Read tool
- Don't skip files or assume they're safe
- Note what files you've reviewed

### Step 2: Map Attack Surface

For each changed file, identify:

**User Input Points:**
- Request parameters, headers, body
- URL/path components
- File uploads
- WebSocket messages
- GraphQL/API inputs

**Data Operations:**
- Database queries (SQL, NoSQL, ORM)
- File system operations
- External API calls
- Cache operations

**Security Controls:**
- Authentication checks
- Authorization/permission checks
- Session management
- Rate limiting
- CSRF protection

**Sensitive Operations:**
- Cryptographic functions
- Password handling
- Token generation
- Payment processing

### Step 3: Security Analysis

Check each category for **every changed file**:

#### Injection Vulnerabilities

- **SQL Injection**: Unparameterized queries, string concatenation
- **Command Injection**: Shell commands with user input
- **Template Injection**: Unsafe template rendering
- **Header Injection**: Unvalidated headers, CRLF injection
- **Path Traversal**: File operations with unsanitized paths
- **NoSQL Injection**: Unvalidated queries in MongoDB, etc.

#### Cross-Site Scripting (XSS)

- Template outputs without escaping
- innerHTML with user content
- Unsanitized data in attributes
- JavaScript template literals with user data

#### Authentication & Authorization

- **Authentication**: Missing auth checks on protected endpoints
- **Authorization**: Authenticated but not authorized (IDOR)
- **Elevation**: Users accessing admin functions
- **Session**: Fixation, hijacking, insecure flags

#### Data Validation

- Missing input validation at boundaries
- Type confusion attacks
- Integer overflow
- Buffer overflow (C/C++, Rust unsafe)

#### Business Logic

- Race conditions (TOCTOU)
- State machine violations
- Numeric overflow in calculations
- Logic flaws in workflows

#### Cryptography

- Weak algorithms (MD5, SHA1 for security)
- Insecure random (Math.random for tokens)
- Hardcoded secrets
- Improper key management

#### Information Disclosure

- Secrets in logs or error messages
- Sensitive data in responses
- Timing attacks
- Stack traces to users

#### Denial of Service

- Unbounded loops or recursion
- Missing pagination
- Regex ReDoS patterns
- Resource exhaustion

#### Configuration

- CSRF protection disabled
- Insecure CORS
- Missing security headers
- Debug mode in production

### Step 4: Verify Issues

For each potential issue:

**Confirm it's real:**
- Check if it's already handled elsewhere
- Look for existing tests covering the scenario
- Read surrounding context
- Verify the code path is reachable

**Don't report if:**
- Already validated upstream
- Protected by middleware
- Test/mock code only
- Existing issue not introduced by this branch

### Step 5: Pre-Conclusion Audit

Before finalizing your findings, you MUST explicitly:

1. **List every file you reviewed** and confirm you read it completely (not just the diff hunk — the full file for context).
2. **List every security category from Step 3** and note, per file, whether you found issues or confirmed it's clean.
3. **List any areas you could NOT fully verify** and explain why (e.g., "could not trace authorization for `/api/export` — the permission class is defined in a file outside this diff").
4. Only then produce your findings.

This step is not optional — it forces the check-every-item discipline that prevents confident "looks clean" reports on code you only skimmed. If you cannot complete the audit, say so explicitly rather than hiding the gap.

### Step 6: Report Findings

Be concise and accurate. Don't invent issues.

## Output Format

For each real issue found:

```
### [Severity] File:Line - Brief description

**Problem:** Clear explanation of the vulnerability or bug

**Evidence:** Why this is a real issue (not already fixed, no test coverage, etc.)

**Impact:** What could happen (data breach, crash, etc.)

**Fix:** Specific, actionable suggestion

**Reference:** OWASP link or standard if applicable
```

**Severity levels:**
- **Critical**: Data breach, RCE, auth bypass
- **High**: IDOR, XSS, SQLi, significant bugs
- **Medium**: Info disclosure, DoS, logic bugs
- **Low**: Edge cases, minor issues

**If nothing significant found:**
```
No security vulnerabilities or bugs found in the changes.

Reviewed files:
- src/api/user.py
- src/models/profile.py
- tests/test_user.py

All inputs are validated, queries are parameterized, and auth checks are present.
```

## Examples

### Example 1: SQL Injection

```
### [Critical] src/api/users.py:45 - SQL injection in user search

**Problem:** User search query concatenates unsanitized input directly into SQL

**Evidence:**
- Line 45: `query = f"SELECT * FROM users WHERE name = '{search_term}'"`
- No parameterization or escaping
- search_term comes directly from request.args
- No test coverage for SQL injection attempts

**Impact:** Attacker can execute arbitrary SQL, dump database, or delete data

**Fix:** Use parameterized query:
```python
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, [search_term])
```

**Reference:** OWASP SQL Injection - https://owasp.org/www-community/attacks/SQL_Injection
```

### Example 2: Authorization Issue

```
### [High] src/api/profiles.py:78 - Missing authorization check

**Problem:** updateProfile() checks authentication but not authorization

**Evidence:**
- Line 78: Only checks if user is logged in
- Does not verify user owns the profile being updated
- User can update any profile by changing profile_id parameter
- No test for unauthorized profile updates

**Impact:** Users can modify other users' profiles (IDOR vulnerability)

**Fix:** Add ownership check:
```python
if profile.user_id != current_user.id and not current_user.is_admin:
    raise PermissionDenied()
```

**Reference:** OWASP A01:2021 - Broken Access Control
```

### Example 3: No Issues Found

```
No security vulnerabilities or bugs found.

**Files reviewed:**
- src/api/search.py - Input validation present, parameterized queries
- src/models/search.py - No user input handling
- tests/test_search.py - Good test coverage including edge cases

All user inputs are validated at API boundary, database queries use
parameterization, and test coverage is comprehensive.
```

## Common Bug Patterns

| Language   | Pattern                         | Issue                          |
| ---------- | ------------------------------- | ------------------------------ |
| Python     | Mutable default args            | Shared state across calls      |
| JavaScript | Missing `await`                 | Returns Promise not value      |
| Go         | Goroutine without WaitGroup     | Resource leaks                 |
| All        | TOCTOU (check-then-act)         | Race conditions                |
| All        | Unclosed resources              | File/connection leaks          |

## Tool Usage

- **Use `git diff main...HEAD`** to get all changes
- **Use Read tool** to examine complete files for context
- **Use Grep tool** to search for dangerous patterns (eval, exec, etc.)
- **Use Task tool with Explore agent** to understand codebase architecture
- **Use LSP tool** to trace function calls and data flow

## Search Patterns for Common Issues

```bash
# SQL injection patterns
grep -r "execute.*format\|execute.*%.*%" .
grep -r "query.*+.*request\|query.*f\"" .

# Command injection
grep -r "os\.system\|subprocess\.*shell=True" .
grep -r "exec\|eval" .

# Hardcoded secrets
grep -ri "password.*=.*['\"][^'\"]\|api_key.*=.*['\"]" .
```

## Pre-Report Checklist

Before finalizing, verify:

- [ ] Reviewed every changed file completely
- [ ] Checked all security categories for each file
- [ ] Verified each reported issue is real (not already handled)
- [ ] Confirmed code paths are reachable
- [ ] Searched for existing tests
- [ ] No false positives included
- [ ] Listed files reviewed

## Important Notes

**Don't:**
- Report style or formatting issues (use linter instead)
- Report issues already present in main branch (unless asked)
- Invent hypothetical issues without evidence
- Report issues already handled by middleware/framework
- Include issues that have test coverage proving they're handled

**Do:**
- Only report real, exploitable issues
- Be specific about file and line numbers
- Provide concrete fix suggestions
- Say "no issues found" if the code is actually secure
- Prioritize by actual risk, not theoretical severity

**Remember:**
- Security > functionality bugs > code quality
- Be thorough but don't waste time on non-issues
- The goal is finding real problems, not maximizing issue count

# Common patterns to flag

Reference patterns for `review-code`. Load this file when a finding looks like one of the patterns below — the example shows the exact shape and the suggested fix style.

## Python/Django — N+1 query

```python
# Bad
for user in users:
    print(user.profile.name)  # query per user

# Good
users = User.objects.prefetch_related('profile')
```

## TypeScript/React — missing effect dependency

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

## Security — SQL injection

```python
# Bad
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
```

## Silent error swallowing (flag by default)

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

## Language-specific traps

| Language   | Pattern                         | Issue                          |
| ---------- | ------------------------------- | ------------------------------ |
| Python     | Mutable default args            | Shared state across calls      |
| JavaScript | Missing `await`                 | Returns Promise not value      |
| Go         | Goroutine without WaitGroup     | Resource leaks                 |
| All        | TOCTOU (check-then-act)         | Race conditions                |
| All        | Unclosed resources              | File/connection leaks          |

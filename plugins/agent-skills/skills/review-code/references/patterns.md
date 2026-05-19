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

## Codebase type aliases — use them instead of bare primitives

When the codebase has a shared alias for a value's shape, new code (including tests) should adopt it.

```python
# Bad — bare dict in a test helper, but the codebase already has a JSONDict alias
def _state(**overrides) -> dict:
    ...

def test_thing():
    captured: dict = {}
    ...

# Good
from app.types import JSONDict  # wherever the codebase keeps shared aliases

def _state(**overrides) -> JSONDict:
    ...

def test_thing():
    captured: JSONDict = {}
    ...
```

Threshold for "established alias": `git grep -E ': (JSONDict|UserId|...) ' -- '*.py'` returns ≥3 hits across adjacent files. Below that, the alias may be experimental — don't force it.

Generalizes to other shapes:

- `dict` / `list` / `tuple` / `set` → typed alias (`JSONDict`, `Headers`, etc.)
- raw `str` for a closed set of values → `Literal["a", "b", "c"]` or `StrEnum`
- raw `int`/`str` IDs → `NewType("UserId", int)` or branded type

Watch for the asymmetric case: production code uses the alias, but a new test helper or test-local variable falls back to the bare primitive. That's the most common slip.

## Trivial helper / premature abstraction

A new method whose body is one statement, takes no arguments beyond `self`, and is called from one site — the helper buys nothing over inlining.

```python
# Smell — 4 lines, single call site, all inputs from self
class Node:
    def run(self) -> None:
        ...
        self._log_complete()

    def _log_complete(self) -> None:
        self.log.info(
            f"Node:{self.name} Completed",
            extra={"node": self.name, "category": self.category},
        )

# Good — inline at the call site
class Node:
    def run(self) -> None:
        ...
        self.log.info(
            f"Node:{self.name} Completed",
            extra={"node": self.name, "category": self.category},
        )
```

Flag when ALL hold:

- Method body ≤ 3 statements (often just 1).
- All inputs are already attributes of `self` (the method doesn't compose arguments).
- Called from ≤ 2 sites in the diff.
- The call site would be equally readable inlined.

**Exempt:** methods that establish a stable extension point with planned subclass overrides in the same diff; methods that hide non-obvious computation.

If the same logging/formatting shape appears at 3+ call sites, keep the helper but move it to a shared mixin/utility and justify it by the call-site count.

## Test-code idioms

### Python — repetitive tests should be parameterized

```python
# Bad — five copies of the same test body
def test_validates_email_a(): assert validate("a@b.co") is True
def test_validates_email_b(): assert validate("a@b") is False
def test_validates_email_c(): assert validate("") is False
def test_validates_email_d(): assert validate("a@") is False
def test_validates_email_e(): assert validate("@b.co") is False

# Good
@pytest.mark.parametrize("addr,expected", [
    ("a@b.co", True),
    ("a@b",    False),
    ("",       False),
    ("a@",     False),
    ("@b.co",  False),
])
def test_validates_email(addr, expected):
    assert validate(addr) is expected
```

Threshold for flagging: ≥3 near-identical tests differing only in inputs/expected.

### Python — tests asserting on log output

```python
# Bad — pins the log string, not the behavior
def test_user_not_found(caplog):
    lookup_user(999)
    assert "user not found: 999" in caplog.text

# Good — assert on the outcome
def test_user_not_found():
    with pytest.raises(UserNotFound):
        lookup_user(999)
```

If logging *is* the contract being tested (e.g., audit log emits a specific structured field), assert on the structured record, not the rendered message:

```python
# Acceptable — the structured field is the contract
record = next(r for r in caplog.records if r.event == "audit.user_lookup")
assert record.user_id == 999
```

### Python — inline imports inside functions

```python
# Bad
def test_thing():
    from myapp.services import thing  # why?
    assert thing() == 42

# Good — import at module top
from myapp.services import thing

def test_thing():
    assert thing() == 42
```

Inline imports are only justified for: circular dependencies (with a comment), optional/heavy deps loaded lazily, or monkeypatch ordering (with a comment). No comment + no obvious reason → flag.

### Python — pytest env-var setup

```python
# Bad — module-level side effect in conftest.py; runs at import time,
# silent on order, lets real env bleed through if `setdefault` is used
import os
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "fakeuser")

# Good — explicit configuration hook, runs before conftest imports
def pytest_configure(config):
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_USER"] = "fakeuser"
```

Two findings hide here:

1. **Hook choice.** `pytest_configure` is the idiomatic env-setup point.
2. **`setdefault` vs `=`.** `setdefault` lets CI-set vars bleed through (`DB_HOST` from a real CI runner reaches the test). Direct assignment forces fakes. Flag any refactor that flips between the two without intent.

## Bundled-refactor smell (split-PR hygiene)

Signals a feature PR has tangled in an independent refactor:

- PR description: "first of N", "split from #X", "introducing X now so PR B can migrate".
- A new module is added *and* every existing call site is touched in the same diff.
- Removing the new module from the diff would still leave a working feature change.

Finding shape:

> [P2] design — bundled refactor
> The diff bundles `<feature>` with the introduction and adoption of `<new module/abstraction>`. The two are independent: `<new module>` is justified by `<future PR>`, not by this diff's behavior change. Split into two PRs so the feature diff stays focused.

## Existing observability infrastructure

Before approving a new `try/catch`, grep the codebase:

```
grep -rn "Sentry\.\|captureException\|report_error\|logger\.\(error\|exception\)" .
```

If a project-wide error reporter exists and the new catch doesn't route through it, flag:

> [P2] error handling — bypasses existing error reporter
> `<file:line>` swallows the error locally. The codebase already routes errors through `<reporter>` (see `<file:line>`). Add `<reporter>.captureException(err)` (or equivalent) before the local fallback so this failure surfaces in the existing dashboards.

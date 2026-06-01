# Common patterns to flag

Reference patterns for `review-code`. Load this file when a finding looks like one of the patterns below — the example shows the exact shape and the suggested fix style.

## Blast radius — a change that breaks code outside the diff

The highest-severity misses are bugs the diff *causes* in a file it never touches. The diff looks self-consistent; the break is at a caller, a sibling reference, or a handler elsewhere. Search the whole repo for what depends on what the diff changed (see "Trace the blast radius" in the agent's Investigation approach).

```python
# In the diff — a template gains a new placeholder:
PROMPT = "Answer for {user} given {history}"   # was: "Answer for {user}"

# NOT in the diff — a second caller formats the same template directly,
# bypassing the helper that supplies `history`:
def quick_answer(user: str) -> str:
    return PROMPT.format(user=user)            # now raises KeyError: 'history'
```

Find it before it ships:

```bash
# template placeholder set changed → who else formats this template?
rg -n 'PROMPT\.format|\.format\(' --type py
# renamed/removed symbol or a contract string literal → grep the OLD value
rg -n 'old_function_name|"identify-resources"'
# structural variant (every .format call regardless of receiver)
ast-grep --pattern '$X.format($$$)' --lang python    # if available; else the rg above
```

Per change-type: **renamed/removed symbol** → grep the old name; **contract string literal** (enum value, event name, placeholder name) → grep the literal; **template placeholder set** → grep `.format`/render sites and other callers; **new/re-raised exception** → grep `except` clauses on the raise→handler path; **changed signature** → grep call sites. Flag only breakage the diff *causes* — not pre-existing issues in those files.

## Python/Django — N+1 query

```python
# Bad
for user in users:
    print(user.profile.name)  # query per user

# Good
users = User.objects.prefetch_related('profile')
```

## Side effect dispatched around a transaction boundary (dual-write)

A transaction commits data *and* fires an external side effect (background job, event, webhook, email, API call). If the dispatch isn't strictly after commit, a worker can race the writer and see no row / a stale row, or a rollback leaves the side effect orphaned. The bug is timing-dependent, so it passes every test that runs the transaction and the worker in the same process.

```python
# Bad — Django/Celery: task enqueued before the row it reads is committed.
# The worker can start before COMMIT and miss the row; a rollback orphans the job.
with transaction.atomic():
    delivery = Delivery.objects.create(...)
process_delivery.delay(delivery.id)        # races the commit

# Good — dispatch only after the transaction commits
with transaction.atomic():
    delivery = Delivery.objects.create(...)
    transaction.on_commit(lambda: process_delivery.delay(delivery.id))
```

The same lens applies to every stack that pairs a DB transaction with a queue or event bus — only the idioms change:

| Stack | Txn boundary | Dispatch to gate | After-commit fix (dir 1) | Reconciler (dir 2) |
|---|---|---|---|---|
| Django + Celery | `transaction.atomic()` | `task.delay()` | `transaction.on_commit(...)` | periodic reaper over the status |
| SQLAlchemy | `session.commit()` | `queue.enqueue()` | `after_commit` event listener | sweeper / outbox |
| Java / Spring | `@Transactional` exit | `kafkaTemplate.send()` | `@TransactionalEventListener(AFTER_COMMIT)` | `@Scheduled` reaper |
| Rails + Sidekiq | transaction block | `Job.perform_async` | `after_commit` callback | sweeper job |
| Node + Prisma/BullMQ | `$transaction(...)` | `queue.add()` | enqueue after it resolves | cron sweep |
| Go | `tx.Commit()` | `producer.Send()` | publish after `Commit()` returns nil | sweeper goroutine |
| Rust (sqlx) | `tx.commit().await` | `queue.publish()` | enqueue after `commit()` is `Ok` | periodic reclaim task |

Flag any enqueue / publish / `.delay` / `.apply_async` / `perform_async` / `kafkaTemplate.send` / outbound HTTP or mail call that reads or references data written in an enclosing (or just-closed) transaction and isn't gated on commit.

### Two directions — check both

**Direction 1 — dispatch before commit (ordering race).** The example above. Dispatch sits inside or straddles the transaction, so the worker can start before COMMIT. Fixed by `on_commit` / an after-commit hook.

**Direction 2 — committed claim with no reconciler (lost-dispatch durability).** Subtler, and it survives a Direction-1 fix. A transaction commits a row into an *in-progress / claimed* status (`PROCESSING`, `LOCKED`, `SENDING`) whose **only** exit is a side effect dispatched *after* the commit. If that dispatch is lost — process crash between commit and dispatch, broker rejection — the row strands in that status forever, because the retry/resolver path filters on the *prior* status, not this one.

```python
# Bad — row committed as PROCESSING; only process_delivery advances it.
# Crash between the commit and .delay() strands it: the resolver only
# re-scans DEFERRED rows, so nothing ever reclaims a stuck PROCESSING row.
with transaction.atomic():
    delivery.status = PROCESSING
    delivery.save(update_fields=["status"])
process_delivery.delay(delivery.id)        # correct ordering, but lossy

# Good — give the in-progress status a reconciler: a periodic reaper that
# re-scans PROCESSING rows older than a timeout (the same shape as a
# stale-task reaper / idempotency lease-reclaim), or a transactional outbox.
```

`on_commit` does **not** fix Direction 2 — the hook is in-process and dies with the crash. **Validation gate (do this before flagging):** grep the repo for a sweeper that already re-scans that status literal in a periodic task (`rg 'status=.*PROCESSING'` across `tasks.py` / scheduled jobs, look for "reap" / "stale" / "reclaim" / lease-expiry). Flag only if none covers the new status — and when one exists for a *sibling* model (e.g. a reaper for `Task` but not for the new `WebhookDelivery`), that's strong evidence the codebase intends this safety net and the new transition simply missed it. **Don't propose `on_commit` as the fix for Direction 2** — name the reaper/outbox; the hook only addresses Direction 1.

## Non-atomic read-modify-write over a row set (TOCTOU)

A "fetch the keys matching a predicate, then mutate/delete those keys in a *separate* statement" sequence is a time-of-check/time-of-use race. Between the read and the write, a concurrent transaction can move a row *out* of the predicate — but the write, keyed only by `id`/`pk`, still hits it. Classic lost-update / phantom-delete. The tell is a fetch filtered on a *mutable state column* whose follow-up write drops that column from its filter.

```python
# Bad — fetch terminal rows, then delete them by id only.
# A row replayed back to PROCESSING between the two statements is still
# in `ids`, so the delete destroys an active delivery.
while True:
    ids = list(
        WebhookDelivery.objects.filter(status__in=terminal, received_at__lt=cutoff)
        .values_list("id", flat=True)[:batch_size]
    )
    if not ids:
        break
    WebhookDelivery.objects.filter(pk__in=ids).delete()   # predicate dropped

# Good — re-apply the predicate on the mutating statement, so a row that
# left `terminal` in the gap is skipped (one extra WHERE term, atomic at the DB).
WebhookDelivery.objects.filter(pk__in=ids, status__in=terminal).delete()
```

**Validation gate (do this before flagging):** confirm the filtered column is actually *mutable for these rows* — grep for another code path that writes that column (`rg 'status\s*=' / .update(status=`, a replay/reopen/retry/requeue action). If nothing else can transition a fetched row back out of the predicate, there is no race and you should not flag it. The shape is language- and stack-agnostic — the anchor is a mutate/delete keyed by a *collection* of keys whose originating read filtered on a mutable column:

- raw SQL: `SELECT id ... WHERE status='done'` then `DELETE ... WHERE id IN (...)`
- Django / SQLAlchemy: `filter(pk__in=ids)` / `where(Model.id.in_(ids))`
- Rails AR: `where(id: ids).delete_all` after `pluck(:id)`
- Node: Prisma `deleteMany({ where: { id: { in: ids } } })`, Knex `whereIn('id', ids).del()`
- Go: `db.Where("id IN ?", ids).Delete(...)` after a `Pluck`/`Select("id")`
- Java/JPA: `deleteAllById(ids)` after `findAll(...)`

The alternative fix to re-applying the predicate is to do it in one set-based statement, or lock the rows with a row lock (`SELECT ... FOR UPDATE` / `select_for_update()`) across the read and write.

### Single-entity variant — check-then-act

The same race over one row instead of a set, and the IN-set greps miss it. A value is read, something changes it, then a decision uses the value captured earlier. **There is no reliable lexical anchor — trace the data flow from the write backward, don't grep the read by name.** The read can be named anything; matching `prior`/`old`/`existing` catches it only by luck.

```python
# Bad #1 — `prior` is read, the row is mutated, then a decision uses stale `prior`.
prior = Branch.objects.filter(repository=repo, name=name).values_list("status", flat=True).first()
branch = service.sync_single_branch(repo, name)        # mutates the row (update_or_create)
if branch.status == ACTIVE and prior != ACTIVE:        # decides on the pre-mutation snapshot
    invalidate_branch_names(repo.organization_id, repo.id)

# Bad #2 — SAME bug, no tell-tale name. `merged_lookup` is read before the row lock,
# so the decision runs on a pre-lock snapshot a concurrent merge webhook already changed.
merged_lookup = self._load_merged_pr_lookup(repo)      # read OUTSIDE the lock
with transaction.atomic():
    branches = Branch.objects.filter(repository=repo).select_for_update()
    for branch in branches:
        desired = self._desired_status(branch, merged_lookup.get(branch.name))  # stale input
        ...                                            # reverts a just-merged branch to ACTIVE

# Good — read the decision inputs inside the same transaction/lock as the write, or
# derive the transition from the write's own before/after instead of a separate read.
```

Anchor on the **write** (`save`/`update`/`upsert`/`delete`, a cache bust, a dispatch, or a branch gating one) and trace back: does it depend on a value read earlier in the scope, before a mutating op, and is that read under the same lock? **Validation gate:** flag only if another path can change that value concurrently *and* the read and the act aren't already under one transaction / row lock. Be honest about severity — when the worst case is a briefly-stale cache that self-heals on the next sync, it's a low-priority nudge, not a blocker.

## Nullable input collapsing into a consequential default

A state/return/branch decision derived from a value that can be null or absent, where the null-guard is folded into the test so that "missing" and "present-but-test-false" produce the **same** branch — and that branch is the consequential one (a terminal/destructive/hiding state, an access decision, a silent skip). The short-circuit quietly equates *unknown* with *no*.

```python
# Bad — last_commit_timestamp is null=True (the provider sets it None when the
# commit-date fetch fails). A branch that IS present on the remote, with a merged
# PR but no known commit time, short-circuits `revived` to False → MERGED, so it's
# hidden from the selector — the exact symptom this code was meant to fix.
revived = (
    branch.last_commit_timestamp is not None
    and branch.last_commit_timestamp > merged_at
)
return Branch.Status.ACTIVE if revived else Branch.Status.MERGED

# Good — decide what the *absent* case should mean, separately from the comparison.
# A branch present on the remote with unknown commit time is safer ACTIVE than MERGED.
if branch.last_commit_timestamp is None:
    return Branch.Status.ACTIVE          # on remote, evidence missing → stay live
return Branch.Status.ACTIVE if branch.last_commit_timestamp > merged_at else Branch.Status.MERGED
```

The shape is language-agnostic — `x?.foo ?? FALLBACK`, `x != null && cond ? A : B`, `coalesce(x, default)` all hide the same question. **Validation gate:** the value must be genuinely nullable (`null=True` / `Optional[...]` / `| None` / an API field that can be omitted — confirm it), and the absent-case branch must be the consequential one. A nullable value defaulting into a harmless neutral state is not a bug. Ask: *should "unknown" really behave like "no" here?*

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

## Incomplete type-dispatch / coercion

A type-mapping function that enumerates some types and returns the value unhandled for the rest. Breaks only on the input that produces an unenumerated type, when that value hits a narrow downstream contract.

```python
# Bad — handles 5 DB scalar types, silently passes everything else through.
# An Interval column yields timedelta → TableSpec's bool|str|float|int|None
# union rejects it → the typed table never attaches, only for queries that
# select a duration. The docstring lists 5 cases and reads "complete".
def _normalize_cell(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return value  # timedelta, memoryview, Enum, … slip through untouched

# Good — add the known-missing branch AND a catch-all so the next schema
# type degrades to a string instead of breaking the contract.
    if isinstance(value, timedelta):
        return str(value)
    ...
    return value if value is None or isinstance(value, (bool, int, float, str)) else str(value)
```

Verify completeness against the *source* of types, not the docstring: `rg 'sa\.(Interval|JSON|ARRAY|Numeric|Enum)\b'` over the schema in scope, and map each column type to a handled branch.

## Time-bomb constants

A hardcoded date or year used as `now`, a contract boundary, or a default. Ships green and silently rots.

```python
# Bad — eval pinned to a frozen date; "this month" answers drift wrong
EVAL_CURRENT_DATE = "2026-05-21"

# Good — either parameterize, or comment the refresh trigger
EVAL_CURRENT_DATE = os.environ.get("EVAL_DATE", date.today().isoformat())
# or, if the date MUST stay fixed for reproducibility:
# Refresh when bumping the eval baseline; tracked in tests/evals/README.md.
EVAL_CURRENT_DATE = "2026-05-21"
```

Flag any string/int literal that looks like a date/year and is named like a "current" / "today" / "now" reference. Same shape for version pins used as "latest" (`LATEST_MODEL = "claude-..."`).

## Fragile path traversal

`Path(__file__).parents[N]` with N≥2, or hardcoded `../../..` strings. Breaks the day someone moves the file — silently, because the new wrong path may still exist.

```python
# Bad — count-the-dots indexing (and the chained .parent.parent.parent variant
# is just as fragile — same count, different syntax)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Better — probe git
REPO_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
)

# Better still — anchor on the installed package
from importlib.resources import files
PACKAGE_ROOT = files("my_package")

# Best — fix the packaging so this isn't needed at all (see sys.path pattern below)
```

If you see `.parents[N]` with N≥2 *and* a `sys.path.insert` next to it, both findings apply.

## `sys.path` manipulation

A new `sys.path.insert(...)` / `sys.path.append(...)` is almost always a smell — the file is reachable through normal imports if packaging is right.

```python
# Bad — manual path hack so a sibling import works under `python tests/evals/diff.py`
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.evals.scoring import MODEL_PRICING_USD_PER_1K  # noqa: E402

# Good — run with `python -m tests.evals.diff`, or wire the recipe to do so:
# just eval-diff: python -m tests.evals.diff "$@"
from tests.evals.scoring import MODEL_PRICING_USD_PER_1K
```

Acceptable cases are narrow: top of a script that's *also* meant to be runnable directly from a checkout. Even there, the fix is usually `python -m <pkg.module>` in the runner / Justfile / Makefile, not the hack.

## Non-root `.gitignore`

Per-directory `.gitignore` files fragment the rules and hide them from anyone scanning `git status`.

```
# Bad — tests/evals/results/.gitignore
*
!.gitignore

# Good — one entry in the repo-root .gitignore
tests/evals/results/*
!tests/evals/results/.gitkeep
```

Flag any new `.gitignore` outside the repo root unless: (a) the directory is a vendored / submoduled subtree where the inner file is upstream's, or (b) the patterns are only meaningful when that directory exists as a working tree (a generated-artifacts area where the `.gitignore` itself is the placeholder). Even (b) is usually better expressed with `.gitkeep` + a root entry.

## Closed two-state value modeled as a string

`bool` is the right type for two-state flags. A string adds a typo surface, a conversion site, and a "what are the legal values?" question for every reader.

```python
# Bad — string with two values, read with == comparisons everywhere
_CASES: list[tuple[str, str, str]] = [
    ("ec2_spend_question", "what's my ec2 spend?", "in"),
    ("weather_in_tokyo",   "what's the weather?",  "out"),
]
def _is_in_scope(label: str) -> bool:
    return label == "in"

# Good — bool, no converter needed
_CASES: list[tuple[str, str, bool]] = [
    ("ec2_spend_question", "what's my ec2 spend?", True),
    ("weather_in_tokyo",   "what's the weather?",  False),
]
```

Flag when a new field, list-element slot, or parameter has exactly two string values that pair up as on/off-style. If three or more states are anticipated, escalate to `StrEnum` / `Literal[...]` (the existing typing rule).

## Positional tuple where field meaning isn't self-evident

```python
# Bad — what do the two floats mean? You have to read the calling code to find out.
MODEL_PRICING_USD_PER_1K: dict[str, tuple[float, float]] = {
    "us.anthropic.claude-sonnet-4-5-...": (0.003, 0.015),
}
in_per_1k, out_per_1k = pricing  # the meaning only surfaces here

# Good — NamedTuple makes the contract local to the type
class ModelPricing(NamedTuple):
    input_per_1k_usd: float
    output_per_1k_usd: float

MODEL_PRICING: dict[str, ModelPricing] = {
    "us.anthropic.claude-sonnet-4-5-...": ModelPricing(0.003, 0.015),
}
```

Flag positional tuples declared in module-level types or returned from public functions when field meaning isn't obvious from context. Inline tuples in a single function body are fine.

## Stdlib reinvention

Handwritten code that replicates an obvious stdlib one-liner.

```python
# Bad — manual ISO 8601 formatting
ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")

# Good
ts = datetime.now(UTC).isoformat()
```

Most common forms:

- `datetime.strftime`/`strptime` ↔ `isoformat`/`fromisoformat`
- Manual JSON path-walks ↔ `json.loads` + dict access
- Handwritten base64/hex ↔ `base64.b64encode` / `bytes.hex()`
- Manual `os.walk` ↔ `pathlib.Path.glob` / `rglob`
- Custom enum via `if` chain ↔ `StrEnum` / `Literal`

Before flagging, name the exact stdlib call and confirm semantics match (timezone, precision, exception type on bad input).

## Python module names with a leading underscore

```
# Bad — looks intentional, isn't
tests/evals/_router_render.py
tests/evals/_cost_agg_render.py

# Good
tests/evals/router_render.py
tests/evals/cost_agg_render.py
```

Leading underscores mark attributes private *inside* a module (`_internal_fn`), not modules themselves — the stdlib reserves `_foo.py` for C-extension companions (`_collections_abc.py`). If a module is package-internal, control re-exports through `__init__.py` instead. Exempt: an `_internal/` package whose `__init__.py` documents the convention.

## Language-specific traps

| Language   | Pattern                         | Issue                          |
| ---------- | ------------------------------- | ------------------------------ |
| Python     | Mutable default args            | Shared state across calls      |
| JavaScript | Missing `await`                 | Returns Promise not value      |
| Go         | Goroutine without WaitGroup     | Resource leaks                 |
| All        | TOCTOU (check-then-act)         | Race conditions                |
| All        | Unclosed resources              | File/connection leaks          |

## Codebase type aliases — use them instead of bare primitives

When the codebase has a shared alias for a value's shape, new code (including tests) should adopt it. The alias name comes from inversion-protocol discovery in *this* repo — `<Alias>` is a placeholder; substitute whatever calibration surfaced.

```python
# Bad — bare dict in a test helper, but the codebase already has an <Alias>
# (discovered via inversion: e.g., a JSON-shaped dict alias with 100+ hits)
def _state(**overrides) -> dict:
    ...

def test_thing():
    captured: dict = {}
    ...

# Good — substitute the alias the calibration ledger surfaced
from app.types import <Alias>

def _state(**overrides) -> <Alias>:
    ...

def test_thing():
    captured: <Alias> = {}
    ...
```

Threshold for "established alias": verification query (preferred order: `ast-grep`, `rg`, `git grep`) returns ≥3 hits in adjacent files OR ≥10 hits repo-wide. The second clause catches diffs that introduce a brand-new directory (no neighbors yet) where the alias is in heavy use elsewhere. Below both thresholds, the alias may be experimental — don't force it.

Generalizes to other shapes (substitute calibration-surfaced names):

- `dict` / `list` / `tuple` / `set` → typed alias (a JSON-dict alias, a `Headers` alias, etc.)
- raw `str` for a closed set of values → `Literal["a", "b", "c"]` or `StrEnum`
- raw `int`/`str` IDs → `NewType(...)` or branded type

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

### Test pins the wired behavior

When a diff threads a new argument, count, or branch through, the test must assert *that specific thing* — not just that the path runs. Otherwise removing the wiring leaves the test green.

```python
# Diff wires `bedrock_client` into the call.
# Bad — exercises the path, never asserts the new arg arrived. Drop the
# `bedrock_client=` kwarg and this test still passes.
def test_invokes(monkeypatch):
    captured = {}
    monkeypatch.setattr(mod, "invoke", lambda **kw: captured.update(kw))
    node.run()
    assert captured["model_id"] == "m"      # only checks the pre-existing arg

# Good — pin the newly-wired argument
    assert captured["bedrock_client"] is fake_client
```

Flag the missing assertion and name the exact call/value to pin. Same shape for a new retry count (`assert planner.call_count == MAX_RETRIES`) or a new branch (assert the branch's distinct side effect).

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

## LLM / prompt-rendering hazards

For code that builds prompts, renders templates over model/user content, or streams model output. These pass tests on clean inputs and fail on real ones. (No dedicated reviewer dispatches for these — the generalist applies them when the diff touches prompt/model code.)

### Template rendering over brace-bearing content

`str.format()` (and `%`-formatting) treat `{...}` in the *data* as placeholders. Untrusted or model-generated content routinely contains braces (JSON `{"k": v}`, SQL `{schema}`, code), so formatting it raises `KeyError`/`ValueError` and crashes the request.

```python
# Bad — user/model text flows through .format(); a brace in it crashes
prompt = TEMPLATE.format(history=chat_history, result=row_json)

# Good — only substitute trusted placeholders; inject untrusted content
# without re-parsing it for braces
prompt = TEMPLATE.replace("{history}", chat_history).replace("{result}", row_json)
# or build with a method that doesn't reinterpret the data (e.g. f-string at a
# single trusted site, or a templating engine with autoescaping)
```

Flag any `.format(...)`/`%`/`.format_map` whose arguments include user input, model output, DB rows, or chat history. Watch for a `.format()` call placed *outside* a fail-open `try` that's supposed to guarantee the path never crashes.

### Structural-tag / sentinel escaping (prompt injection)

When a prompt delimits sections with sentinels (`<chat_history>…</chat_history>`, `### SYSTEM ###`), untrusted content placed inside must have those sentinels escaped — otherwise a crafted message closes the section early or forges a new one (prompt injection), and any logic that locates the section by `find("<tag>")` breaks.

```python
# Bad — user text dropped between sentinels unescaped
block = f"<chat_history>{user_text}</chat_history>"

# Good — neutralize the sentinel set in untrusted content first
block = f"<chat_history>{escape_sentinels(user_text)}</chat_history>"
```

Flag when a new sentinel/structural tag is introduced but the escaping routine (or its allow-list) isn't updated to cover it.

### Self-closing delimiter

Wrapping content in a delimiter that the content itself can contain ends the wrapper early.

```python
# Bad — response often contains a ```sql ... ``` fence, which closes this one
judge_input = f"```\n{response_text}\n```"

# Good — use a delimiter the payload can't contain (longer/random fence,
# or a non-Markdown sentinel)
fence = "`" * 8
judge_input = f"{fence}\n{response_text}\n{fence}"
```

### Streaming / finalization on the error path

A streamed response usually shows a loading indicator that a `finally`/finalize step clears. If the model call can raise *before* finalize runs, the indicator sticks forever.

```python
# Bad — exception skips the line that clears the indicator
streaming_message = start_stream()
result = invoke_model(...)         # raises → indicator never cleared
streaming_message.finalize()

# Good — finalize in a finally / context manager
async with finalize_on_exit(streaming_message):
    result = invoke_model(...)
```

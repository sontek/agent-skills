---
name: optimize-perf
description: Apply performance improvements with before/after benchmarks. Use when asked to "optimize this", "make it faster", "speed this up", "profile and fix", or when the user wants perf fixes applied (not just reviewed). Runs `review-perf` to find candidates, then for each fix writes a benchmark, applies the change, re-measures, and reverts on regression. Companion to `review-perf` (which only finds issues); distinct from `auto-review-code` (which applies generic fixes without wall-clock measurement).
---

# Optimize Performance

Loop: run `review-perf` → for each fix, benchmark current → apply → re-benchmark → keep if faster, revert if not. Produces a single end-of-run report with measured before/after numbers for every applied fix.

The review phase delegates to the `review-perf` skill, which delegates to the `perf-reviewer` agent in isolated context. **This skill owns only the apply loop with benchmarking.** Issue finding and severity scaling live in `review-perf` / `perf-reviewer`; don't re-implement them here.

## When to use

- "Optimize this endpoint", "make this worker faster", "profile and fix"
- User wants perf fixes applied with proof they actually help
- Pre-deploy perf pass on a service or worker

## When NOT to use

- Find-only perf review — use `review-perf` directly
- Generic code cleanup — use `auto-review-code`
- Django ORM perf with TDD (query-count assertions, not wall-clock) — use `auto-review-code`, which already handles N+1 with TDD
- Schema / migration / SQL-layer perf — use `review-code` (dispatches `sql-reviewer`), then plan migration changes manually

## Modes

Same as `review-perf`. Pick one before starting; default `branch`.

- **`branch` (default)** — Scope is branch changes vs. main.
- **`paths`** — Scope is an explicit list of files reviewed as-is. Requires the invoker to provide the list.

## Why benchmarks, not just tests

`auto-review-code` already handles perf findings via TDD: assert query count for N+1, assert bounded behavior for unbounded loops. That works when the regression is **structural** (one query vs N).

This skill handles findings where the regression is **wall-clock**: an O(n²) loop that ran in 800ms now runs in 80ms, a blocking I/O call replaced by an async client. The win is only real if measured. A benchmark proves the fix actually moved the number — and locks in the gain against future regression.

If the finding is cleanly testable as a structural assertion (query count, item count, allocations), prefer `auto-review-code` for that finding and let this skill handle the wall-clock ones.

## Benchmark discipline

For each fix:

1. **Pick a benchmark harness.** In order of preference, use what already exists in the repo:
   - **Python:** `pytest-benchmark` if installed (`pip show pytest-benchmark`); otherwise `timeit` in a short script under `tests/perf/`.
   - **Go:** `go test -bench=. -benchmem` against a `*_test.go` benchmark function in the same package.
   - **Node:** existing harness if present (e.g. `vitest bench`, `benchmark.js`); otherwise a one-shot script using `performance.now()`.
   - **Generic CLI:** `hyperfine` if installed; otherwise `time` with `--repeat`.
2. **Write a benchmark that exercises the suspect code with realistic input.** Use the caller's volume hint (10k items, 500 concurrent reqs) when available; otherwise default to an input size that exercises the issue (1k for O(n²), 100 for per-item API calls).
3. **Run before.** Record the median of ≥5 runs. If the harness reports variance, capture that too.
4. **Apply the fix.**
5. **Run after.** Same harness, same input, ≥5 runs, median.
6. **Decide:**
   - **Keep** if after < before by a meaningful margin (default: ≥20% faster, or ≥50ms absolute on a request-path operation). Note the delta in the log.
   - **Revert both fix and benchmark** if after ≥ before, OR if the speedup is below the threshold AND the change isn't otherwise behavior-preserving (e.g. it adds complexity for no measurable gain).
   - **Keep without benchmark** only when the fix is structurally obvious (replacing a blocking sync call with an async call on an already-async path; replacing `list.append` in a loop with `extend`). State this explicitly in the log as `benchmark: skipped (structural)`.

### When benchmark infrastructure isn't available

- **No harness installed and `tests/perf/` does not exist:** create a single `tests/perf/test_<scope>_bench.py` (or language equivalent) on first use; commit it with the fix. Do NOT block on standing up CI integration — local benchmarks are enough.
- **Benchmark is prohibitively slow to write** (requires non-trivial fixtures, a running service, real upstreams): flag the finding for manual review instead of auto-applying. Don't fake a benchmark.
- **Finding is in test code itself:** apply directly, no meta-benchmark needed.

## Auto-apply policy

A finding is **auto-applied** when ALL of these hold:

1. Severity is P1, P2, or P3 (P0 escalates — see "Hard-stop on P0").
2. Fix is local: ≤5 files AND ≤~50 LOC of changes (excluding the benchmark).
3. Fix does NOT introduce new dependencies, public-API changes, or config schema changes.
4. Fix is concrete: the agent named the exact transformation, not "consider refactoring."
5. A benchmark was written and the after measurement met the keep threshold (or `benchmark: skipped (structural)` was justified above).

Otherwise: add to the **flagged-for-approval** bucket with a dossier (see `auto-review-code` for the six-field format: Proposal / What the user sees / Pros / Cons / Recommendation / To apply). Over-flagging is cheap; over-applying a "fix" that doesn't measurably help is expensive.

## Hard-stop on P0

`review-perf` emits its findings on the same P0–P3 ruler as `review-code`. Any P0 stops the loop — show the finding and wait. (`perf-reviewer` rarely emits P0; P0 perf usually means "production is on fire," which is a different conversation.)

## Loop structure

For each round (cap at 3 — perf fixes converge faster than generic review):

1. **Review phase.** Invoke the `review-perf` skill with the configured mode and scope. It returns findings tagged P0–P3.
2. **Triage findings.** Classify each as `p0-halt`, `auto-apply`, or `flag-for-approval`.
3. **Check oscillation.** For each `auto-apply`, check if the same fingerprint was already attempted in a previous round. If yes, move to `flag-for-approval` with a note ("oscillation: previously attempted in round N, fix did not stick or kept regressing").
4. **For each `auto-apply` fix:**
   - Write the benchmark.
   - Run before.
   - Apply the fix.
   - Run after.
   - Keep or revert per the threshold above.
   - Run the repo's normal test suite for the changed files (`pytest path/`, `go test ./...`, etc.) to catch behavior regressions. If tests fail, revert the fix and the benchmark; flag the finding.
5. **Log the round** to `.claude/optimize-perf-log.md` (see format below).
6. **Check exit conditions.**

## Exit conditions

- **Convergence** — A round produced zero auto-applied fixes (kept). Normal success.
- **Max rounds** — 3 rounds completed.
- **P0 hard-stop** — Escalate to the user.
- **Oscillation** — A finding was attempted twice without sticking; move to flagged with a note and exit if it oscillates a third time.
- **Behavior-regression loop** — Three consecutive fixes fail the test suite. Stop and escalate.

## Fingerprint format

Same as `auto-review-code`:

```
{relative_path}:{start_line}|{category}|{short_summary_slug}
```

Where `category` is one of `blocking-io`, `algo`, `batching`, `unbounded-mem`, `caching`, `concurrency`, `micro`.

## State log format

Write to `.claude/optimize-perf-log.md` at the repo root. Overwrite on each invocation.

```markdown
# Optimize-perf log

Mode: branch
Scope: main..HEAD (4 files)
Harness: pytest-benchmark
Started: 2026-05-28T14:00:00Z

## Round 1

- [P1] app/api/orders.py:42 | blocking-io | requests-in-async-handler — perf-reviewer
  - benchmark: tests/perf/test_orders_bench.py::test_get_order_status
  - before: 412ms (median of 5)
  - after:  38ms  (median of 5)
  - delta:  -91% (kept)
  - tests:  pytest app/api/test_orders.py — passed

- [P1] app/workers/sync.py:88 | batching | per-item-api-call — perf-reviewer
  - benchmark: tests/perf/test_sync_bench.py::test_sync_batch
  - before: 22.1s (10k items)
  - after:  1.8s  (10k items, single batch call)
  - delta:  -92% (kept)
  - tests:  pytest app/workers/test_sync.py — passed

- [P2] app/api/config.py:24 | caching | repeated-toml-parse — perf-reviewer
  - benchmark: tests/perf/test_config_bench.py::test_config_endpoint
  - before: 8.2ms
  - after:  8.0ms
  - delta:  -2% (REVERTED — below 20% threshold)

## Round 2

- (no findings)

## Exit: convergence (round 2)
```

## Final summary (emit to user)

After the loop exits, emit a single user-facing summary as rendered markdown (no outer code fence).

````markdown
## Optimize-perf complete

**Mode:** branch | **Scope:** main..HEAD | **Rounds:** 2 (converged)

**Applied (2 fixes, measured improvements):**
- `app/api/orders.py:42` — replaced `requests.get` with `httpx.AsyncClient` on async handler
  - **412ms → 38ms (-91%)** — `tests/perf/test_orders_bench.py::test_get_order_status`
- `app/workers/sync.py:88` — replaced per-item loop with batch endpoint
  - **22.1s → 1.8s on 10k items (-92%)** — `tests/perf/test_sync_bench.py::test_sync_batch`

**Reverted (1 — did not meet threshold):**
- `app/api/config.py:24` — caching the TOML parse saved 2%, below the 20% threshold; reverted.

**Flagged for approval (0)**

**Test suite:** all passing after applied fixes.

Log: `.claude/optimize-perf-log.md`

Next: review the applied diffs, run the benchmarks once more in CI if you want a corroborating data point, and commit.
````

## User override mid-run

If the user interrupts with a correction ("lower the keep threshold to 10%", "don't touch the workers", "stop benchmarking, just apply the obvious ones"), honor it for the remainder of the run, note it in the log, and continue.

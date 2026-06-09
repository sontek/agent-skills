# Reviewer selection

The canonical reviewer-selection rules shared by `review-code` and `review-pr`. Each
skill resolves its own scope, then selects reviewers per the rules here. This is the
**single source of truth** so the two skills can't drift apart — they did once
(review-pr's table fell behind review-code's, and a Terraform or raw-SQL diff drew no
specialist at all). Add a row here and both skills inherit it.

## Always dispatch

**`code-reviewer`** and **`security-auditor`** run on every review.

## Add specialists by domain

Add a specialist only when the changed files touch its domain — running one with
nothing in scope just adds noise:

| Signal in changed files | Add agent |
|---|---|
| Django code (`models.py`, `views.py`, `urls.py`, DRF, `from django`) | `django-access-reviewer`, `django-perf-reviewer` |
| Application-tier code in any backend stack — Flask, FastAPI, Starlette, **Django views/services/tasks/workers**, Go `net/http` / gin / echo, Node express / fastify, plain Python services/workers | `perf-reviewer` |
| `.github/workflows/*.yml` | `gha-security-reviewer` |
| IaC (`*.tf`, `*.tofu`, `infra/`) | `iac-reviewer` |
| DB layer (migrations, raw SQL, `import sqlalchemy`/`sqlmodel`, `cursor.execute`/`text(`) | `sql-reviewer` |

## Overlap is the backstop, not a conflict

`sql-reviewer` and `django-perf-reviewer` can both match a Django-ORM diff that also
touches raw SQL; dispatch both and let the skill's coalesce/dedup step treat the
agreement as corroboration. The same applies to `perf-reviewer` co-firing with
`django-perf-reviewer` or `sql-reviewer`, including on Django code, where all three
may run. `perf-reviewer` leads with the application tier (algorithmic / async /
batching / caching) but also surfaces the **language-agnostic** shapes that cross
into the data layer — a per-item round-trip in a loop (including DB writes), an
unbounded fetch into memory — naming the generic problem and fix; the data-layer
reviewers own the exact idiom (`bulk_update` vs `update`, index DDL, locking). When
two reviewers land the same finding, dedup collapses it into one and treats the
agreement as corroboration. Don't suppress `perf-reviewer` to avoid the overlap —
the overlap is the backstop.

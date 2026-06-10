# Reviewer selection

The canonical reviewer-selection rules shared by `review-code` and `review-pr`. Each
skill resolves its own scope, then selects reviewers per the rules here. This is the
**single source of truth** so the two skills can't drift apart — they did once
(review-pr's table fell behind review-code's, and a Terraform or raw-SQL diff drew no
specialist at all). Add a row here and both skills inherit it.

## Always dispatch

**`code-reviewer`** and **`security-auditor`** run on every review.

One **focused cross-region lane** also runs on every review:

- **`context-consistency-reviewer`** — *inward:* does the change fit the constraints of
  the code around it (an enclosing guard's documented constraint, sibling branches, a
  shared latest-state, a new instance vs its siblings, a comment it now contradicts)?

It targets the skill's documented weak spot — recall on the **non-salient**
"locally-correct, contextually-wrong" family, where the governing context sits outside
the diff hunk and the broad `code-reviewer` loses attention to the easier, salient
finding. Validated against platform#3832 (a constraint-violating branch hidden in a
"done-looking" feature diff): the omnibus caught it ~1/3 across 18 runs regardless of
rule wording; this focused lane caught it 3/3 at P2 with no false positive on the fixed
version. It is single-purpose **by design** — narrowness is what gives it the attention
the omnibus can't spare; do not broaden it into a general reviewer. Findings flow through
the same coalesce/dedup + verifier path as every other lane (overlap with `code-reviewer`
is corroboration). Cost note: one extra parallel agent per review; if cost matters on
trivial diffs, gate it to changes above a few lines rather than dropping it — recall, not
false positives, is this skill's failure mode.

> **Candidate (not dispatched): `blast-radius-reviewer`** — the *outward* twin (does the
> change break a dependent elsewhere?). Built and on disk, but **held**: end-to-end the
> omnibus already catches blast-radius whenever the diff carries any signal (a salient
> rename 2/2; a unit change with a param rename 3/3) — its step-2 trace is strong, so a
> standalone lane is churn on every case reproducible. Lane 2's *only* distinct value was
> a **concept** gap, not an attention gap: the semantic-drift class (meaning shifts behind
> a stable signature — units/sign/sortedness/tz/nullability) was absent from step-2, which
> a unit A/B confirmed (the pre-change step-2 wording missed it 3/5). That concept has been
> **folded into step-2** of `code-reviewer.md` (validated 5/5 vs 3/5 — see the
> `blast_radius` eval), so the lane's value now lives in the omnibus and the lane stays
> unwired. Revisit a standalone lane only if a *non-salient* blast-radius miss is found
> that the live omnibus fails over N runs. Full result in `evals/bot-miss-audit-2026-06.md`.

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

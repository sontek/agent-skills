The honest "before": step-2 blast-radius as it shipped *before* the semantic-drift
bullet was added — its trigger list was keyed on renamed/removed symbols, changed
literals, template placeholders, new exceptions, and changed signatures. Every trigger
has a **token to grep**; there is no entry for a *meaning* change behind a stable
signature (unit/sign/sortedness/tz/nullability), which is exactly the class with nothing
to anchor on.

2. Trace the blast radius. A diff can break code it never touches. When the diff changes any of the following, search the **whole repo** — not just the changed files — for what depends on it, and read each hit:
   - a **renamed or removed symbol** (function, variable, attribute, config key) → grep the *old* name;
   - a **changed string literal that is a contract** (enum/category value, event name, a template placeholder name) → grep the literal;
   - a **template's placeholder set** (a `{key}` added or removed) → grep render / `.format` sites and any *other* caller of that template, including ones that bypass the modified code path;
   - a **new or re-raised exception type** → grep the `except` clauses on the path from the raise site to its intended handler;
   - a **changed function/method signature or contract** (parameters, return shape, exceptions raised) → grep its call sites.

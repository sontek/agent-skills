The narrow pre-broadening wording (the "before"): the reviewer flagged comment
drift only when the diff GREW a surface, plus the generic why-not-what aim. A
comment that is actively false about code the diff did not grow falls through.

- Comments explain *why* (non-obvious constraints), not *what* (obvious from code).
- **Surface metadata that no longer describes the code.** When the diff extends a
  surface — adds a method to a class, an entry to a registry, a route to a router,
  a field to a schema, a case to a dispatcher — read the prose that *describes*
  that surface and check it still matches: the docstring, a `description=` string,
  a header comment that counts items. A docstring listing two methods when there
  are now three is silent drift: the diff is correct but the surface around it now
  lies. Flag it and quote the stale text.

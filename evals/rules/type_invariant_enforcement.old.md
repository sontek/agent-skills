Faithful pre-rule guidance (the "before"): code-reviewer's Design section had
abstraction-justification questions and the named-type rules, and said nothing
about enforcing a type's invariant or making invalid states unconstructible.

- Are abstractions justified by current use, not speculative future use?
- Use named types (`NamedTuple` / `@dataclass`, `Literal` / `StrEnum`, `NewType`)
  instead of bare primitives where the codebase has an established alias.

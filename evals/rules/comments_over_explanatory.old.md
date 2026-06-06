### comments.docstring-rationale (severity: medium)

Module or function docstrings that explain WHY a design was chosen over alternatives, restate what the code does, or run past a one-sentence purpose statement.

```python
# Bad
"""Helper for X.

This module does Y rather than Z because Z is async and has side effects we
don't want. The parity test fires if a future refactor moves auto-injection.
"""

# Good
"""Helper for X."""
```

Flag when:

- A module docstring runs > 3 lines AND the first sentence already states the purpose.
- A function docstring runs > 2 lines arguing for the design, or an inline comment runs > 2 lines explaining design intent rather than a non-obvious WHY.

**Exempt:** hidden constraints, subtle invariants, workarounds with bug citations, public-API contracts with versioned interfaces.

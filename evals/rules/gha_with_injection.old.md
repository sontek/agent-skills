**Rule: GitHub Actions expression injection.** `${{ }}` is dangerous in `run:`
blocks because the shell expands it. It is **safe** in `if:`, `with:`, and
`env:` — those are evaluated by the Actions runtime, not the shell, and passed
as string parameters. Only flag `${{ }}` of attacker-controlled data used
directly inside a `run:` block.

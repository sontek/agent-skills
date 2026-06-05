**Rule: Fragile path traversal.** Flag `Path(__file__).parents[N]` with N≥2, or
hardcoded relative `../../..` strings. These break the day someone moves the
file. Prefer a stable anchor like `importlib.resources` or a git-root probe.

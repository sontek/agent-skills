---
name: uv
description: Use `uv` instead of `pip` / `python` / `venv` for Python work in repos that have adopted uv. Use when running Python scripts (`uv run`), adding dependencies (`uv add`), creating standalone scripts with inline dependency metadata (`uv init --script`), or managing the Python build backend (`uv_build`). Triggered by mentions of `uv`, inline script metadata blocks (`# /// script ... ///`), `uv.lock`, `pyproject.toml` with `[tool.uv]`, or any Python script Claude is about to run in a uv project.
---

# uv

Use `uv` for Python in projects that have adopted it. `uv` replaces `pip`, `python`, `python -m venv`, and `python -m pip` with a single fast tool.

## When NOT to use this skill

If the repo uses **Poetry** (`poetry.lock`, `[tool.poetry]` in `pyproject.toml`), **pip-tools** (`requirements.in` + `requirements.txt`), or **Pipenv** (`Pipfile`), follow that toolchain instead. Don't introduce `uv` into a project that hasn't adopted it.

Signals that a repo uses `uv`:
- `uv.lock` present
- `pyproject.toml` has `[tool.uv]` or `requires = ["uv_build"]` in `[build-system]`
- README references `uv run` / `uv add`

## Quick reference

```bash
uv run script.py                       # Run a script
uv run --with requests script.py       # Run with ad-hoc dependency
uv run python -m ast foo.py >/dev/null # Verify syntax without writing __pycache__
uv add requests                        # Add dependency to project
uv init --script foo.py                # Create script with inline metadata
uv lock --script foo.py                # Lock script's deps to foo.py.lock
```

## Inline script metadata

Standalone scripts can declare their own dependencies (PEP 723):

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests<3",
#   "rich",
# ]
# ///

import requests
from rich import print
```

Then just: `uv run script.py`. No virtualenv to manage; uv resolves and caches the deps automatically.

For an executable shebang script:

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["httpx"]
# ///
import httpx
print(httpx.get("https://example.com").text)
```

```bash
chmod +x myscript
./myscript
```

See [scripts.md](scripts.md) for full script-running details (locking, reproducibility, alternative indices).

## Build backend

For pure Python packages, use `uv_build`:

```toml
[project]
name = "my-package"
version = "0.1.0"
requires-python = ">=3.12"

[build-system]
requires = ["uv_build>=0.9.28,<0.10.0"]
build-backend = "uv_build"
```

For C-extension modules, use `hatchling` instead — `uv_build` is pure-Python only.

See [build.md](build.md) for project structure, namespace packages, and file inclusion rules.

## Common tasks

| Task | Command |
|---|---|
| Run a project script | `uv run script.py` |
| Run without installing the project itself | `uv run --no-project script.py` |
| Pin a Python version | `uv run --python 3.10 script.py` |
| Add a dependency to `pyproject.toml` | `uv add requests` |
| Add a dev dependency | `uv add --dev pytest` |
| Add to a script's inline metadata | `uv add --script foo.py requests rich` |
| Sync the env from `pyproject.toml` + `uv.lock` | `uv sync` |
| Update lockfile | `uv lock` |
| Run a tool without installing into the project | `uvx ruff check .` |

## Syntax check without writing `__pycache__`

`python -m py_compile` writes pycache files into the source tree. To check syntax without that side effect:

```bash
uv run python -m ast script.py >/dev/null
```

Exit code is non-zero on syntax error; stderr has the parse error.

## Reproducibility

Pin the dependency resolution date in inline metadata so a script run today resolves the same way next year:

```python
# /// script
# dependencies = ["requests"]
# [tool.uv]
# exclude-newer = "2026-05-01T00:00:00Z"
# ///
```

## Adapted from

- [mitsuhiko/agent-stuff](https://github.com/mitsuhiko/agent-stuff/tree/main/skills/uv)

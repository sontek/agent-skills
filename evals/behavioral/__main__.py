"""CLI for the behavioral skill-test harness.

    python -m behavioral list                 # show specs
    python -m behavioral run                   # run all specs
    python -m behavioral run commit            # run named spec(s)
    python -m behavioral run --runs 3 --keep   # more reps; keep work dirs

Each `claude -p` run costs tokens — default --runs is 2 (min for a discrimination
signal). Raise it for confidence; lower variance is not free.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from .specs import SPECS, run_spec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="behavioral", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list available specs")
    r = sub.add_parser("run", help="run specs")
    r.add_argument("names", nargs="*", help="spec names (default: all)")
    r.add_argument("--runs", type=int, default=2, help="reps per arm (default 2)")
    r.add_argument("--keep", action="store_true", help="keep temp work dirs")
    args = p.parse_args(argv)

    if args.cmd == "list":
        for name, spec in SPECS.items():
            print(f"  {name:16} {spec.doc}")
        return 0

    names = args.names or list(SPECS)
    unknown = [n for n in names if n not in SPECS]
    if unknown:
        print(f"unknown spec(s): {', '.join(unknown)}\navailable: {', '.join(SPECS)}", file=sys.stderr)
        return 2

    work_root = Path(tempfile.mkdtemp(prefix="behavioral-"))
    failures = 0
    try:
        for name in names:
            if not run_spec(SPECS[name], args.runs, work_root):
                failures += 1
    finally:
        if args.keep:
            print(f">> kept work dir: {work_root}")
        else:
            shutil.rmtree(work_root, ignore_errors=True)

    if failures:
        print(f"{failures} spec(s) did not discriminate")
        return 1
    print("all specs discriminate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

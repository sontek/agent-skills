#!/usr/bin/env bash
# Same recipe, but a `trap ... EXIT` is registered immediately after bring-up, so the
# teardown runs on every exit path — including the validation `exit 2`. The
# acquire/release pairing holds on all exits, so the stack is never left running.
set -euo pipefail

test-deps-up                                # acquire: start postgres + localstack
trap test-deps-down EXIT                    # release guaranteed on every exit path
[[ "$WORKERS" =~ ^[0-9]+$ ]] || exit 2
run_pytest -n "$WORKERS"

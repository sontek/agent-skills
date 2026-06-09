#!/usr/bin/env bash
# A test recipe: bring up the Docker test stack, run the suite, tear it down. A
# validation guard sits BETWEEN bring-up and tear-down, so on bad input the recipe
# exits with the containers still running — the matching teardown is never reached.
# Same acquire/release-skipped-by-a-non-local-exit shape as a lock with no finally,
# expressed in shell with `exit`.
set -euo pipefail

test-deps-up                                # acquire: start postgres + localstack
[[ "$WORKERS" =~ ^[0-9]+$ ]] || exit 2      # early exit — stack still running
run_pytest -n "$WORKERS"
test-deps-down                              # release: not reached when validation fails

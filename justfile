# Task runner for the sontek-skills repo.
# Node is pinned via .mise.toml (24.15.0 — satisfies promptfoo's engines).
# Recipes run through `mise exec` so they use that Node regardless of how your
# shell is set up; requires `just` (https://just.systems) and mise.
#
# The eval suite (regression + cross-language overfit testing for our detection
# rules) lives in evals/. Run `just` with no arguments to list recipes.
#
# Provider: recipes default to Bedrock (AWS credential chain, no Anthropic key).
# Pass `anthropic` to switch, e.g. `just eval anthropic`. Override the Bedrock
# model/region with EVAL_BEDROCK_MODEL / AWS_REGION.

evals := "evals"
promptfoo := "./node_modules/.bin/promptfoo"

# List available recipes.
_default:
    @just --list

# Ensure the pinned Node (via mise) and the toolchain are present.
_ensure:
    @mise install
    @cd {{evals}} && [ -x {{promptfoo}} ] || mise exec -- npm install

# Force a fresh install of the pinned toolchain.
install:
    mise install
    cd {{evals}} && mise exec -- npm install

# Sanity-check the fixture -> test generator (no tokens spent).
gen:
    cd {{evals}} && mise exec -- node tests.gen.js

# Print the rule text the suite will use — for `current`, sliced live from the
# agent files; for old, `RULE_VARIANT=old just show`.
show:
    cd {{evals}} && mise exec -- node tests.gen.js --show

# Run the suite against the CURRENT (live) rule wording. [provider: bedrock|anthropic]
# Regression: every catch_ fixture must FLAG, every safe_ must stay CLEAN.
eval provider="bedrock": _ensure
    cd {{evals}} && mise exec -- {{promptfoo}} eval --filter-providers {{provider}}

# Run the suite against the frozen pre-generalization (over-fit) wording.
# Cross-language catch_ fixtures are EXPECTED to fail — that gap is the point.
eval-old provider="bedrock": _ensure
    cd {{evals}} && RULE_VARIANT=old mise exec -- {{promptfoo}} eval --filter-providers {{provider}}

# A/B both wordings back to back (old "before", then current "after").
ab provider="bedrock": (eval-old provider) (eval provider)

# Same as eval/eval-old/ab, for Bedrock models that reject `temperature` (Opus 4.6+).
# Set EVAL_BEDROCK_MODEL (e.g. us.anthropic.claude-opus-4-8) and AWS_REGION=us-west-2.
eval-notemp provider="bedrock": _ensure
    cd {{evals}} && mise exec -- {{promptfoo}} eval -c promptfooconfig.notemp.yaml --filter-providers {{provider}}
eval-old-notemp provider="bedrock": _ensure
    cd {{evals}} && RULE_VARIANT=old mise exec -- {{promptfoo}} eval -c promptfooconfig.notemp.yaml --filter-providers {{provider}}
ab-notemp provider="bedrock": (eval-old-notemp provider) (eval-notemp provider)

# Open the promptfoo result grid in the browser.
view: _ensure
    cd {{evals}} && mise exec -- {{promptfoo}} view

# Validate the promptfoo config (loads prompt.js + tests.gen.js; no API calls).
validate: _ensure
    cd {{evals}} && mise exec -- {{promptfoo}} validate

# --- Comment-quality A/B (review-pr comment-style) -------------------------
# A separate suite that asks the model to WRITE a PR comment and grades it,
# rather than detecting a bug. A/B the live comment-style.md ("after") against
# the frozen variants/comment-style.baseline.md ("before"). See
# evals/comment-quality/README.md.

cq := "comment-quality/promptfooconfig.yaml"

# Generate + list the comment-quality cases (no tokens spent).
gen-cq:
    cd {{evals}}/comment-quality && mise exec -- node tests.gen.js

# Show which guidance file each variant binds to (live vs frozen baseline).
show-cq:
    cd {{evals}}/comment-quality && mise exec -- node tests.gen.js --show

# Validate the comment-quality config (no API calls).
validate-cq: _ensure
    cd {{evals}} && mise exec -- {{promptfoo}} validate -c {{cq}}

# Run the comment-quality suite against the CURRENT (live) comment-style wording.
eval-cq provider="bedrock": _ensure
    cd {{evals}} && mise exec -- {{promptfoo}} eval -c {{cq}} --filter-providers {{provider}}

# Run it against the frozen pre-edit baseline ("before").
eval-cq-old provider="bedrock": _ensure
    cd {{evals}} && RULE_VARIANT=old mise exec -- {{promptfoo}} eval -c {{cq}} --filter-providers {{provider}}

# A/B both wordings back to back (baseline "before", then live "after").
ab-cq provider="bedrock": (eval-cq-old provider) (eval-cq provider)

# Behavioral skill tests — run a skill end-to-end via headless `claude -p` and
# check it DISCRIMINATES from baseline (skill on/off, or edit before/after).
# Complements the promptfoo suite (detection rules); covers triggering + procedure.
# Spends tokens (real claude runs). [names...] or empty for all; --runs N, --keep.
#   just behavioral list
#   just behavioral run commit
#   just behavioral run --runs 3
behavioral *ARGS:
    cd {{evals}} && uv run --no-project python -m behavioral {{ARGS}}

# Remove the local toolchain and promptfoo's eval cache/output.
clean:
    cd {{evals}} && rm -rf node_modules .promptfoo output.json

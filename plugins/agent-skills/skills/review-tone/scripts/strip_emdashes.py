#!/usr/bin/env python3
"""Strip em-dashes, en-dashes, and `--` (used as an em-dash) from text.

Em/en-dashes are an AI tell in short human writing, so the review-tone skill
removes them and rewrites each affected sentence to flow without the dash.

Reads text from stdin, emits JSON to stdout:

    {
      "stripped": "<text with every dash collapsed to a single space>",
      "affected_sentences": ["<original sentence that held a dash>", ...],
      "count": <number of affected sentences>
    }

`stripped` is a placeholder, not finished prose: wherever a dash was
load-bearing (a pause, a parenthetical, a connector), the surviving text reads
awkwardly. That is the point. `affected_sentences` flags exactly those
sentences so the skill can rewrite them to sound human. A single hyphen in a
compound (mid-size, line-level) is left alone; only em (U+2014), en (U+2013),
and a literal `--` are treated as dashes.
"""

import json
import re
import sys

DASH = re.compile(r"\s*(?:—|–|--)\s*")
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def main() -> int:
    text = sys.stdin.read()

    affected = [
        sentence.strip()
        for sentence in SENTENCE.split(text)
        if sentence.strip() and DASH.search(sentence)
    ]

    stripped = DASH.sub(" ", text)

    json.dump(
        {
            "stripped": stripped,
            "affected_sentences": affected,
            "count": len(affected),
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

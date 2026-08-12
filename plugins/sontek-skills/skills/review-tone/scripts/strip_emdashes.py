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

Two exemptions, because a dash isn't always a slop tell:
- A markdown table row (`| a | b |`) is left untouched entirely. A dash there
  is data notation, not prose — a "no measurement" placeholder or a numeric
  range — and flagging the whole row (or worse, a row glued to the paragraph
  around it, since neither ends in terminal punctuation) produces an unusable
  "affected sentence".
- An en-dash directly between two digits (`4.3–6.0s`) is a numeric range, not
  a pause. Left alone wherever it appears, table or prose.
"""

import json
import re
import sys

DASH = re.compile(r"\s*(?:—|–|--)\s*")
NUMERIC_RANGE = re.compile(r"(?<=[\d.])–(?=\d)")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
BLOCK_START = re.compile(r"^\s*(?:#{1,6}\s|\||[-*+]\s|\d+[.)]\s)")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\-])")
RANGE_PLACEHOLDER = ""


def _protect_ranges(s: str) -> str:
    return NUMERIC_RANGE.sub(RANGE_PLACEHOLDER, s)


def _restore_ranges(s: str) -> str:
    return s.replace(RANGE_PLACEHOLDER, "–")


def segments(text: str):
    """Split into rewrite units.

    A markdown table row or block marker (heading, list item) is its own
    unit, so a dash inside one never glues onto the surrounding paragraph.
    Plain paragraph lines accumulate and split further on terminal
    punctuation, same as before.
    """
    out = []
    para = []

    def flush():
        if not para:
            return
        joined = " ".join(para)
        for s in SENTENCE.split(joined):
            s = s.strip()
            if s:
                out.append(s)
        para.clear()

    for line in text.split("\n"):
        if not line.strip():
            flush()
            continue
        if TABLE_ROW.match(line) or BLOCK_START.match(line):
            flush()
            out.append(line.strip())
        else:
            para.append(line.strip())
    flush()
    return out


def _strip_line(line: str) -> str:
    if TABLE_ROW.match(line):
        return line
    return _restore_ranges(DASH.sub(" ", _protect_ranges(line)))


def main() -> int:
    text = sys.stdin.read()

    affected = []
    for seg in segments(text):
        if TABLE_ROW.match(seg):
            continue
        if DASH.search(_protect_ranges(seg)):
            affected.append(seg)

    stripped = "\n".join(_strip_line(line) for line in text.split("\n"))

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

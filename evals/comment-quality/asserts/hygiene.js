/**
 * Deterministic comment hygiene — no grader, no tokens.
 *
 * Fails the output if it carries either AI tell the comment-style guidance
 * forbids:
 *   1. an em-dash (—), en-dash (–), or a `--` used as a dash (the review-tone
 *      mechanical rule),
 *   2. a label/severity prefix (`blocking —`, `suggestion —`, `nit:`, `P1`,
 *      `Sec-High`, …) — weight belongs in the prose, not a tag.
 *
 * A single hyphen in a compound word (mid-size, line-level) is fine.
 */
module.exports = (output) => {
  const text = String(output);
  const problems = [];

  if (/[—–]/.test(text)) problems.push("contains an em-dash or en-dash");
  // ` -- ` (whitespace both sides) is a typed em-dash substitute. This
  // deliberately does NOT match `--flag` (CLI options have no trailing space).
  if (/\s--\s/.test(text)) problems.push("contains a `--` used as a dash");

  const labelPrefix =
    /^\s*(blocking|suggestion|nit|question|praise|issue|warning|sec[- ]?high|sec[- ]?med|p[0-9])\b\s*[—:-]/i;
  // Check the first non-empty line — a prefix tag lives at the start.
  const firstLine = (text.split("\n").find((l) => l.trim().length) || "").trim();
  if (labelPrefix.test(firstLine)) {
    problems.push(`opens with a label prefix: "${firstLine.slice(0, 40)}…"`);
  }

  return {
    pass: problems.length === 0,
    score: problems.length === 0 ? 1 : 0,
    reason: problems.length === 0 ? "clean" : problems.join("; "),
  };
};

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

  // DIAGNOSTIC, NOT A GATE. `pass` is always true; the signal is `score`.
  //
  // The skill does not ask the model to write dash-free prose in one shot — it
  // generates the comment, then runs review-tone's strip_emdashes.py, which
  // FLAGS the affected sentences for a rewrite pass (its own output is an
  // explicit placeholder, not finished prose). This harness models only the
  // generation turn, and it pastes in a comment-style.md that itself contains
  // ~57 em-dashes for the model to mirror. Gating on dash-freedom here therefore
  // failed most outputs in every arm, flooring `success` to 0 and masking the
  // llm-rubric signal the suite exists to measure.
  //
  // Scoring it without gating keeps the number visible (regressions still show
  // up in the metric) without letting it drown the rubric. Real dash compliance
  // is enforced by the skill's strip-and-rewrite loop, which this suite does not
  // model; gating it would need a second model turn.
  const clean = problems.length === 0;
  return {
    pass: true,
    score: clean ? 1 : 0,
    reason: clean ? "clean" : `[diagnostic, non-gating] ${problems.join("; ")}`,
  };
};

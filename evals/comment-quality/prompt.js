/**
 * Builds the chat prompt for one comment-quality scenario.
 *
 * Unlike the detection suite (which asks for a FLAGGED/CLEAN verdict), this
 * suite asks the model to actually WRITE the PR review comment it would post,
 * given a coalesced finding + code context and the review-pr `comment-style`
 * guidance. The asserts then grade that comment (deterministic hygiene + an
 * llm-rubric on the property the edit is supposed to produce).
 *
 * Plain JS, not a Nunjucks template, to match the sibling suite: scenario
 * `context` can contain literal `{{ }}` / `${{ }}` and must pass through
 * verbatim. tests.gen.js has already wrapped the var values in {% raw %}.
 */
module.exports = async function commentPrompt({ vars }) {
  const { guidance, finding, context } = vars;

  const system = [
    "You are a senior engineer leaving ONE review comment on a teammate's pull request.",
    "A review sub-agent has handed you a finding it believes is real and worth raising; you have already verified the claim and decided to post.",
    "Write the single comment you would leave, anchored at the given location.",
    "Output ONLY the comment body as it would appear on GitHub (Markdown). No preamble, no 'Here is', no severity label, no sign-off.",
    "",
    "Follow this comment-style guidance exactly:",
    '"""',
    String(guidance).trim(),
    '"""',
  ].join("\n");

  const user = [
    "Finding (from the review sub-agent — its wording, not yet rewritten for the author):",
    '"""',
    String(finding).trim(),
    '"""',
    "",
    "Code / diff context for the anchored location:",
    "",
    "~~~",
    String(context).replace(/~~~/g, "≈≈≈"),
    "~~~",
    "",
    "Write the review comment.",
  ].join("\n");

  return [
    { role: "system", content: system },
    { role: "user", content: user },
  ];
};

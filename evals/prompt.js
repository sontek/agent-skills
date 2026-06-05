/**
 * Builds the chat prompt for one (rule, snippet) pair.
 *
 * Deliberately plain JS — NOT a Nunjucks template — because fixtures contain
 * literal `${{ ... }}` (GitHub Actions) and `{{ }}` sequences that Nunjucks
 * would try to interpolate and silently corrupt. promptfoo calls this function
 * with the test's `vars`; whatever array of messages we return is sent as-is.
 *
 * The reviewer is asked to apply exactly ONE rule and end with a machine-
 * readable verdict line, so the suite can assert with a deterministic
 * `contains` check instead of paying for an LLM grader on every case.
 */
module.exports = async function reviewPrompt({ vars }) {
  const { rule, snippet, language } = vars;

  const system = [
    "You are a focused code reviewer. You are given exactly ONE review rule and ONE code snippet.",
    "Decide only whether THIS rule fires on THIS snippet. Ignore unrelated issues and style nits.",
    "Apply the rule's validation gate faithfully: do not flag a snippet the rule explicitly exempts.",
    "",
    "Reason in at most three sentences, then output a FINAL line that is exactly one of:",
    "VERDICT: FLAGGED   (the issue the rule describes is present in the snippet)",
    "VERDICT: CLEAN     (the issue the rule describes is not present)",
    "",
    "The rule:",
    '"""',
    String(rule).trim(),
    '"""',
  ].join("\n");

  const user = [
    `Language: ${language}`,
    "Snippet under review:",
    "",
    "~~~" + language,
    String(snippet).replace(/~~~/g, "≈≈≈"),
    "~~~",
  ].join("\n");

  return [
    { role: "system", content: system },
    { role: "user", content: user },
  ];
};

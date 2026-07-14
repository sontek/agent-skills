/**
 * Generates one promptfoo test per scenario file for the comment-quality A/B.
 *
 *   scenarios/<name>.json  ->  one test
 *
 * Each scenario provides the finding + code context and the rubric(s) that
 * describe the property a good comment must have. Every test also gets the
 * deterministic hygiene assert (no em/en-dash, no label prefixes).
 *
 * GUIDANCE WORDING (the A/B axis):
 *   variant=current (default): the FULL `comment-style.md` is read LIVE from the
 *     review-pr skill. No copy to drift — edit the live reference, re-run, and
 *     the suite reflects it. This is the "after".
 *   variant=old (RULE_VARIANT=old): the frozen pre-edit snapshot in
 *     variants/comment-style.baseline.md — the honest "before". An edit "helped"
 *     when a scenario the baseline gets wrong goes right under current, and the
 *     control scenario stays right under both (no regression).
 *   variant=<name>: any other value binds variants/comment-style.<name>.md, so a
 *     change that bundles several edits can be split into one arm per edit and
 *     each one's contribution attributed separately.
 */
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const SCENARIOS = path.join(ROOT, "scenarios");
const VARIANT = process.env.RULE_VARIANT || "current";

const LIVE_GUIDANCE = path.join(
  ROOT,
  "../../plugins/sontek-skills/skills/review-pr/references/comment-style.md",
);

function guidancePath() {
  if (VARIANT === "current") return LIVE_GUIDANCE;
  const name = VARIANT === "old" ? "baseline" : VARIANT;
  const p = path.join(ROOT, `variants/comment-style.${name}.md`);
  if (!fs.existsSync(p)) {
    throw new Error(`RULE_VARIANT=${VARIANT} but no such variant file: ${p}`);
  }
  return p;
}

function guidanceText() {
  return fs.readFileSync(guidancePath(), "utf8").trim();
}

function generateTests() {
  const guidance = guidanceText();
  // promptfoo Nunjucks-renders var VALUES; scenario context / guidance can hold
  // literal {{ }} or ${{ }}. Wrap so they emit verbatim.
  const raw = (s) => `{% raw %}${s}{% endraw %}`;

  const tests = [];
  for (const fname of fs.readdirSync(SCENARIOS).sort()) {
    if (!fname.endsWith(".json")) continue;
    const sc = JSON.parse(fs.readFileSync(path.join(SCENARIOS, fname), "utf8"));

    const assert = [
      // Deterministic, no grader: AI tells + label prefixes the comment must not
      // carry. Reported as the `hygiene` metric, NOT a gate — see asserts/hygiene.js
      // for why (the skill strips dashes in a second pass this harness doesn't model).
      { type: "javascript", value: "file://asserts/hygiene.js", metric: "hygiene" },
    ];
    // Each scenario rubric is an llm-rubric describing the property the comment
    // must exhibit. The discriminating scenarios are written so the baseline
    // guidance plausibly fails them and the edited guidance passes.
    for (const r of sc.rubrics || []) {
      assert.push({ type: "llm-rubric", value: r });
    }

    tests.push({
      description: `${sc.name} [${sc.kind || "mismatch"}] -> ${VARIANT}`,
      vars: {
        guidance: raw(guidance),
        finding: raw(sc.finding),
        context: raw(sc.context),
      },
      assert,
      metadata: { scenario: sc.name, kind: sc.kind || "mismatch", variant: VARIANT },
    });
  }
  return tests;
}

module.exports = generateTests;

// `node tests.gen.js`        -> counts (no tokens spent)
// `node tests.gen.js --show` -> print which guidance file binds for this variant
if (require.main === module) {
  if (process.argv[2] === "--show") {
    const p = guidancePath();
    console.log(`variant=${VARIANT} reads guidance from:\n  ${p}`);
    console.log(`(${fs.readFileSync(p, "utf8").split("\n").length} lines)`);
    process.exit(0);
  }
  const tests = generateTests();
  console.log(`variant=${VARIANT}  total=${tests.length}`);
  for (const t of tests) console.log(`  - ${t.description}  (asserts: ${t.assert.length})`);
}

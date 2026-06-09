/**
 * Generates one promptfoo test per fixture file.
 *
 * Convention (no config edits needed to add a case — just drop a file):
 *   fixtures/<rule>/<language>/<catch|safe>_<name>.<ext>
 *     catch_* -> the rule MUST fire        -> expect VERDICT: FLAGGED
 *     safe_*  -> the rule MUST NOT fire     -> expect VERDICT: CLEAN
 *
 * RULE WORDING:
 *   variant=current (default): the rule text is sliced LIVE out of the agent
 *     file named in rules/sources.json (read-only). This binds the regression
 *     suite to what actually ships — there is no copy to drift. Edit the live
 *     agent file, re-run, and the suite reflects the change.
 *   variant=old (RULE_VARIANT=old): reads the frozen pre-generalization wording
 *     from rules/<rule>.old.md — the permanent "before" for an A/B that proves a
 *     generalization closed a gap without adding false positives.
 */
const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const FIXTURES = path.join(ROOT, "fixtures");
const RULES = path.join(ROOT, "rules");
const VARIANT = process.env.RULE_VARIANT || "current";

const SOURCES = JSON.parse(fs.readFileSync(path.join(RULES, "sources.json"), "utf8"));
const LANG_LABEL = { python: "python", go: "go", typescript: "typescript", gha: "yaml" };

// Slice the live rule out of its agent file, between two anchor lines
// (start inclusive, end exclusive).
function sliceLive(rule) {
  const src = SOURCES[rule];
  if (!src) throw new Error(`rules/sources.json has no entry for "${rule}"`);
  const lines = fs.readFileSync(path.join(ROOT, src.file), "utf8").split("\n");
  const startIdx = lines.findIndex((l) => l.includes(src.start));
  if (startIdx === -1) {
    throw new Error(`start anchor not found for "${rule}" in ${src.file}: ${src.start}`);
  }
  let endIdx = lines.findIndex((l, i) => i > startIdx && l.includes(src.end));
  if (endIdx === -1) {
    // A declared end anchor that no longer resolves means the rule was reworded
    // and the slice would silently run to EOF, swallowing every later rule.
    // Fail loudly instead so anchor drift is caught, not shipped.
    if (src.end) {
      throw new Error(`end anchor not found for "${rule}" in ${src.file} (anchor drift?): ${src.end}`);
    }
    endIdx = lines.length;
  }
  return lines.slice(startIdx, endIdx).join("\n").trim();
}

function ruleText(rule) {
  if (VARIANT === "old") {
    const oldPath = path.join(RULES, `${rule}.old.md`);
    if (fs.existsSync(oldPath)) return fs.readFileSync(oldPath, "utf8");
    return sliceLive(rule); // no frozen snapshot — fall back to live
  }
  return sliceLive(rule);
}

function expectedFor(filename) {
  if (filename.startsWith("catch")) return "FLAGGED";
  if (filename.startsWith("safe")) return "CLEAN";
  return null;
}

function generateTests() {
  const tests = [];
  for (const rule of fs.readdirSync(FIXTURES).sort()) {
    const ruleDir = path.join(FIXTURES, rule);
    if (!fs.statSync(ruleDir).isDirectory()) continue;
    const rule_md = ruleText(rule);

    for (const langDir of fs.readdirSync(ruleDir).sort()) {
      const langPath = path.join(ruleDir, langDir);
      if (!fs.statSync(langPath).isDirectory()) continue;
      const language = LANG_LABEL[langDir] || langDir;

      for (const fname of fs.readdirSync(langPath).sort()) {
        const expected = expectedFor(fname);
        if (!expected) continue;
        const snippet = fs.readFileSync(path.join(langPath, fname), "utf8");
        // promptfoo Nunjucks-renders var VALUES (renderVarsInObject). Rule text
        // and fixtures contain literal `${{ }}` / `{{ }}` (GitHub Actions) that
        // would blow up the parser, so wrap them so Nunjucks emits them verbatim.
        const raw = (s) => `{% raw %}${s}{% endraw %}`;
        tests.push({
          description: `${rule}/${langDir}/${fname} -> ${expected}`,
          vars: { rule: raw(rule_md), snippet: raw(snippet), language },
          assert: [{ type: "contains", value: `VERDICT: ${expected}` }],
          metadata: { rule, language: langDir, expected, variant: VARIANT },
        });
      }
    }
  }
  return tests;
}

// Guard against verdict leaks: a fixture must never state the answer the model is
// supposed to reach. A comment that says "CLEAN" or "FLAGGED" (the literal output
// verdict) lets the model copy it instead of reasoning to it — which silently props
// up the safe-case false-positive guard and can mask a real over-flag (this bit the
// `default_ignores_explicit_null` safe set: a hidden Haiku FP only surfaced once the
// "CLEAN" comment was removed). Scans every fixture for the verbatim uppercase
// verdict tokens; `just gen` / CI fail on a hit. Describe the code's behaviour, not
// the expected verdict (see README "Adding a rule").
function checkVerdictLeaks() {
  const VERDICT = /\b(CLEAN|FLAGGED)\b/;
  const leaks = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(p);
        continue;
      }
      fs.readFileSync(p, "utf8")
        .split("\n")
        .forEach((line, i) => {
          if (VERDICT.test(line)) leaks.push(`${path.relative(ROOT, p)}:${i + 1}: ${line.trim()}`);
        });
    }
  };
  walk(FIXTURES);
  return leaks;
}

module.exports = generateTests;

// `node tests.gen.js`          -> counts + verdict-leak check (no tokens spent)
// `node tests.gen.js --show`   -> print the sliced live rule text to eyeball the binding
if (require.main === module) {
  if (process.argv[2] === "--show") {
    for (const rule of Object.keys(SOURCES)) {
      if (rule.startsWith("_")) continue;
      console.log(`\n===== ${rule}  (variant=${VARIANT}) =====`);
      console.log(ruleText(rule));
    }
    process.exit(0);
  }
  const tests = generateTests();
  const byRule = {}, byLang = {};
  for (const t of tests) {
    byRule[t.metadata.rule] = (byRule[t.metadata.rule] || 0) + 1;
    byLang[t.metadata.language] = (byLang[t.metadata.language] || 0) + 1;
  }
  console.log(`variant=${VARIANT}  total=${tests.length}`);
  console.log("by rule:", byRule);
  console.log("by language:", byLang);

  const leaks = checkVerdictLeaks();
  if (leaks.length) {
    console.error(
      "\nVERDICT LEAK — a fixture states the output verdict (CLEAN/FLAGGED) in its text,\n" +
        "letting the model copy the answer instead of reasoning to it. Reword to describe\n" +
        "the code's behaviour, not the expected verdict (see README \"Adding a rule\"):",
    );
    for (const l of leaks) console.error("  " + l);
    process.exit(1);
  }
}

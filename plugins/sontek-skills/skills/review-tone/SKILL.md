---
name: review-tone
description: Write, rewrite, and review prose (docs, READMEs, PR descriptions, review comments, commit messages, error messages, release notes, tool descriptions) so it reads clear and controlled, then human, not AI-generated. Two layers — STE-flavored writing (active voice, simple tenses, sentence caps, one name per concept, no semicolons/phrasal verbs) and AI-slop hygiene (no em-dashes, no filler/marketing words, no label prefixes, no editorializing, plain words over jargon, lead with the point, no AI attribution). Use when asked to draft docs/PR text/release notes/error messages from scratch, "make this not sound like AI", "does this read human", "review the tone", "strip the em-dashes", "de-slop this", or check STE/controlled-language violations. Not for marketing copy, essays, chat replies, or anything needing a persuasive voice (sales emails, landing pages) — those own their voice and call this only for the slop-hygiene layer. Final pass for sales-email-*, create-pr, review-pr comments.
argument-hint: '<text to write/rewrite/review, or a path/description of what to clean>'
allowed-tools: Read, Write, Bash
metadata:
  spec: ASD-STE100 Issue 9 (January 2025), STE-flavored mode, plus AI-slop hygiene rules
---

# Review Tone

Make prose read clear and controlled, then make it read human. Two layers, applied together by default:

- **Layer 1 — STE-flavored writing**, adapted from ASD-STE100 (the aerospace controlled-language standard): grammar discipline that removes ambiguity. Condensed below; full catalog and strict mode in [references/ste-rules.md](references/ste-rules.md).
- **Layer 2 — AI-slop hygiene**: removes the tells that mark text as AI-generated or robotic, regardless of medium.

Applies to documentation, READMEs, pull-request text, review comments, commit messages, error messages, release notes, tool descriptions, and system prompts. Not code, identifiers, or command syntax.

**Voice-sensitive text** — sales emails or anything with a persona defined elsewhere (e.g. `sales-email-*`'s `voice.md`): apply Layer 2 only. Layer 1's tense/sentence-length/active-voice constraints flatten a deliberately built voice — skip them there. This is the *only* carve-out. Everything else, PR descriptions and review comments included, gets both layers in full: expand every contraction, split every semicolon, and rewrite every passive with a nameable actor into active voice, even where the passive reads more natural to you — "flows fine as-is" is not a Layer 1 exemption, only rules 3.3 (stative participle) and 3.6 (actor unknown/irrelevant) are.

## Modes

- **write** — compose new text straight to both layers. Default when asked to draft a README, error message, release note, or PR description from scratch — this is why the skill triggers on writing tasks, not only on explicit review requests.
- **rewrite** — convert an existing draft. Keep every fact, number, condition, and scope qualifier; never drop one to satisfy a length cap — keep the longer sentence and flag it instead.
- **review** — do not rewrite. Output a table (`Rule | Original | Fix`), one row per violation across both layers, then one line on anything left alone and why.

Each mode runs two ways: **standalone** (the user hands you text or a target — report what you'd change and why, then give the result) or **final pass** (another skill calls this before shipping a draft — apply the rules and return clean text, surfacing only what the calling skill should know about).

## Layer 1 — condensed

- Active voice; only simple tenses (no present perfect, no modal stacks: "it may help to improve" → "this improves").
- One name for one action ("check" or "verify", not both) and one meaning per word.
- Max 20 words/instruction, 25/descriptive sentence; one topic per paragraph, max 6 sentences.
- No semicolons, no contractions, no dropped articles, no "-ing" as a main verb, no phrasal verbs (spin up, dive into), no nominalizations ("perform an analysis" → "analyze").
- Multi-word nouns ≤ 3 words; define abbreviations at first use.
- Numbered vertical lists for steps, one action per item, condition before command.

## Layer 2 — AI-slop hygiene

### A. No em-dashes (the strongest tell)

Em-dashes (`—`), en-dashes (`–`), and double-hyphens (`--`) used as em-dashes are the clearest AI tell in short human writing. Remove all of them. Three exemptions, because a dash isn't always a slop tell: a single hyphen in a compound word (`mid-size`, `line-level`); a dash inside a markdown table row (a "no measurement" placeholder or data notation, not prose); and an en-dash directly between two digits (`4.3–6.0s`, a numeric range). The stripper script already knows about all three — leave those alone even if you're tempted to "clean up" a table.

Run the stripper to find and remove them mechanically:

```
cat draft.txt | python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/strip_emdashes.py
```

(Use the Bash tool. If `${CLAUDE_PLUGIN_ROOT}` isn't set, the script is at `skills/review-tone/scripts/strip_emdashes.py` under the plugin.) The JSON response lists `affected_sentences` — the originals that held a dash. Each now reads awkwardly because the dash was load-bearing (a pause, a parenthetical, a connector). **Rewrite each one** to flow naturally with commas, periods, parentheses, or a restructured clause. Pick the version that sounds most like the author, not the one closest to the original shape. Do not reintroduce any em/en-dash or `--`. Verify zero remain before finishing.

Running the script *is* the verification — eyeballing the text is not a substitute, and "I checked it" without having run it is not either. Run the stripper on the exact final text, and re-run it after any edit you make to that text, however small.

(Note: a product's own marketing/UI style guide may *want* spaced em-dashes — that's a deliberate house style for published copy, not 1:1 writing. This pass is for emails, comments, commits, and prose that should read as one person talking.)

### B. Cut AI-tell filler

These words and openers inflate without adding meaning. If you're reaching for one, the sentence isn't done: *revolutionary, supercharge, unleash, delight, magic/magical, elevate, seamless, robust, leverage, just, simply, easy/easily, game-changing, next-level, empower, cutting-edge, "we're excited to", "I hope this email finds you well", "I noticed that", "per my previous email", "it's worth noting that".* Don't write "AI-powered" — name what the thing actually does.

Also cut **redundant restatement**: saying the same conclusion two or three ways for emphasis ("the worst place for a false green… passes having validated nothing… grades nothing"). State it once, in its sharpest form. Repetition reads as padding, not weight.

### C. Signal weight in prose, not labels

Drop tag/label prefixes (`blocking —`, `suggestion —`, `nit —`, `P1`, `Sec-High`) and `Recommendation:` headers. Convey importance the way a person does, in the sentence itself: a must-fix reads as must-fix because the consequence is concrete ("this throws when `order` is None") and you say "before merge" in plain words; a minor point opens with "small one:"; a question just asks. The severity is self-evident from the consequence; you don't need to stamp it.

### D. Don't editorialize or narrate posture

Cut phrases that narrate the act of writing instead of saying the thing: "worth a conscious call", "merits a conscious sign-off", "mostly flagging", "this is purely about X discipline", "the default quietly changed", "just flagging since". Also cut phrases that hand the reader a decision they obviously already own: "the approach is up to you", "I'll leave that to you", "your call", "feel free to". When you've raised a question, the reader knows the answer is theirs — stating it is filler. State the point and its consequence and let the prose carry the weight.

### E. Plain words over jargon

Describe what the thing does in concrete terms instead of reaching for shorthand. "A new route is public unless someone adds the decorator" beats "the default is now fail-open." Only use a term of art if the reader would plainly recognize it, and even then say the plain version first. The CI-color metaphor is a common offender — "the suite passes green" says no more than "the suite passes" ("green" is redundant), and "green/red" can read as jargon; prefer plain "passes" / "fails".

### F. Lead with the bottom line, stay concise

First sentence states the point. No preamble, no restating what the reader already knows, no walking them through mechanism before they learn what you want. One idea per paragraph.

### G. No AI attribution

Never "As an AI", "Generated by Claude", or tool-attribution footers, in the text or anywhere it's posted. (This matches the repo's commit/PR convention.)

## Verify

Both layers are mechanical checks, not eyeballing:

```
cat draft.txt | python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/strip_emdashes.py   # Layer 2, em-dashes
python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/ste_lint.py draft.md                # Layer 1, flavored: target under 2.5/100w
python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/ste_lint.py --strict draft.md       # Layer 1, strict: target under 1.5/100w
```

Fix the reported categories and lint again, at most two passes. Report the final score with the text. Don't present text as clean without having run both scripts on the exact final version.

`passive_voice` is a floor, not a verdict: the script exempts a fixed list of known-stative participles (`required`, `protected`, `supported`, …) per rule 3.3, but that list can't be exhaustive — a word like "held" or "verified" can be genuine passive (rewrite it, if the actor is known) or a permitted stative/actor-irrelevant use (leave it), and only reading the sentence tells you which. Don't rewrite every flagged passive on the count alone.

If you cannot run commands, use this checklist for Layer 1 (Layer 2 has no substitute for the stripper — flag it as unverified):

1. Any instruction over 20 words, or any other sentence over 25? Split it.
2. Any semicolon? Replace with a period.
3. Any contraction? Expand it.
4. Any present perfect ("has/have received") or modal stack? Use a simple tense.
5. Any passive voice with a known actor? Make it active.
6. Any "-ing" main verb, nominalization ("perform an analysis"), or phrasal verb ("spin up")? Replace with a plain verb.
7. Any multi-word noun of four or more words? Unpack it.
8. Same thing named two ways? Pick one name.

## Output

- **Standalone mode:** briefly list what you changed and why (grouped by layer/rule is fine), then give the full cleaned text. If the text was already clean, say so rather than inventing changes.
- **Final-pass mode (called by another skill):** apply the rules and return the clean text; surface only changes the calling skill should know about (e.g., sentences you rewrote around a dash).
- **Review mode:** the violations table plus the one-line note on what was left alone, no rewritten text unless asked for one too.

Don't change the author's meaning, claims, or structure beyond what these rules require. Discipline, not a rewrite.

---

Arguments: `$ARGUMENTS`

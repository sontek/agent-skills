---
name: review-tone
description: Review and fix the tone of a piece of writing so it reads like a sharp human, not an AI or a form. Strips em-dashes and other AI tells, cuts filler and robotic hedging, and reports what changed plus the cleaned text. Use on emails, PR descriptions, review comments, commit messages, docs, or any prose — "review the tone", "does this read human", "strip the em-dashes", "de-slop this". Invoked as the final pass by the sales-email-* and create-pr skills, and to clean review-pr's comments; pairs with review-pr's comment-style for PR comments.
argument-hint: '<text to review, or a path/description of what to clean>'
allowed-tools: Read, Write, Bash
---

# Review Tone

Make a piece of writing read like a sharp human wrote it. This is the medium-agnostic hygiene layer: it removes the tells that mark text as AI-generated or robotic, regardless of whether the text is an email, a PR comment, a commit message, or a doc. Skills that own a *voice* (the `sales-email-*` family) or a *medium* (`review-pr`'s `comment-style.md`) layer their specifics on top of these rules.

Run it two ways:
- **Standalone:** the user hands you text (or points at a draft) and wants it cleaned. Report what you'd change and why, then give the cleaned version.
- **As a final pass:** another skill calls you on a draft before it ships. Apply the rules and return clean text.

## The rules

### 1. No em-dashes (the strongest tell)

Em-dashes (`—`), en-dashes (`–`), and double-hyphens (`--`) used as em-dashes are the clearest AI tell in short human writing. Remove all of them. A single hyphen in a compound word (`mid-size`, `line-level`) is fine — leave those.

Run the stripper to find and remove them mechanically:

```
cat draft.txt | python3 ${CLAUDE_PLUGIN_ROOT}/skills/review-tone/scripts/strip_emdashes.py
```

(Use the Bash tool. If `${CLAUDE_PLUGIN_ROOT}` isn't set, the script is at `skills/review-tone/scripts/strip_emdashes.py` under the plugin.) The JSON response lists `affected_sentences` — the originals that held a dash. Each now reads awkwardly because the dash was load-bearing (a pause, a parenthetical, a connector). **Rewrite each one** to flow naturally with commas, periods, semicolons, parentheses, or a restructured clause. Pick the version that sounds most like the author, not the one closest to the original shape. Do not reintroduce any em/en-dash or `--`. Verify zero remain before finishing.

(Note: a product's own marketing/UI style guide may *want* spaced em-dashes — that's a deliberate house style for published copy, not 1:1 writing. This pass is for emails, comments, commits, and prose that should read as one person talking.)

### 2. Cut AI-tell filler

These words and openers inflate without adding meaning. If you're reaching for one, the sentence isn't done: *revolutionary, supercharge, unleash, delight, magic/magical, elevate, seamless, robust, leverage, just, simply, easy/easily, game-changing, next-level, empower, cutting-edge, "we're excited to", "I hope this email finds you well", "I noticed that", "per my previous email", "it's worth noting that".* Don't write "AI-powered" — name what the thing actually does.

Also cut **redundant restatement**: saying the same conclusion two or three ways for emphasis ("the worst place for a false green… passes having validated nothing… grades nothing"). State it once, in its sharpest form. Repetition reads as padding, not weight.

### 3. Signal weight in prose, not labels

Drop tag/label prefixes (`blocking —`, `suggestion —`, `nit —`, `P1`, `Sec-High`) and `Recommendation:` headers. Convey importance the way a person does, in the sentence itself: a must-fix reads as must-fix because the consequence is concrete ("this throws when `order` is None") and you say "before merge" in plain words; a minor point opens with "small one:"; a question just asks. The severity is self-evident from the consequence; you don't need to stamp it.

### 4. Don't editorialize or narrate posture

Cut phrases that narrate the act of writing instead of saying the thing: "worth a conscious call", "merits a conscious sign-off", "mostly flagging", "this is purely about X discipline", "the default quietly changed", "just flagging since". Also cut phrases that hand the reader a decision they obviously already own: "the approach is up to you", "I'll leave that to you", "your call", "feel free to". When you've raised a question, the reader knows the answer is theirs — stating it is filler. State the point and its consequence and let the prose carry the weight.

### 5. Plain words over jargon

Describe what the thing does in concrete terms instead of reaching for shorthand. "A new route is public unless someone adds the decorator" beats "the default is now fail-open." Only use a term of art if the reader would plainly recognize it, and even then say the plain version first. The CI-color metaphor is a common offender — "the suite passes green" says no more than "the suite passes" ("green" is redundant), and "green/red" can read as jargon; prefer plain "passes" / "fails".

### 6. Lead with the bottom line, stay concise

First sentence states the point. No preamble, no restating what the reader already knows, no walking them through mechanism before they learn what you want. One idea per paragraph.

### 7. No AI attribution

Never "As an AI", "Generated by Claude", or tool-attribution footers, in the text or anywhere it's posted. (This matches the repo's commit/PR convention.)

## Output

- **Standalone mode:** briefly list what you changed and why (grouped by rule is fine), then give the full cleaned text. If the text was already clean, say so rather than inventing changes.
- **Final-pass mode (called by another skill):** apply the rules and return the clean text; surface only changes the calling skill should know about (e.g., sentences you rewrote around a dash).

Don't change the author's meaning, claims, or structure beyond what these rules require. Tone hygiene, not a rewrite.

---

Arguments: `$ARGUMENTS`

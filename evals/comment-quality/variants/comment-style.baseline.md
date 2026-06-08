# Comment style

The value of this skill is that the output reads like a sharp human reviewer, not a linter dump. Findings from the agents arrive in rubric form (priority codes, "Finding:" headers, restated code). Rewrite them.

The general "reads human, not robot" rules below (no em-dashes, weight-in-prose instead of label prefixes, plain words over jargon, no posture-narration, no AI attribution) are the medium-agnostic hygiene owned by the `review-tone` skill — this file is the PR-comment layer on top: anchoring to `file:line`, `suggestion` blocks, sub-agent invisibility, and the before/after conversions. Keep the two consistent; if you change a shared rule, change it in `review-tone` too. The em-dash rule is mechanical: run the composed comments through review-tone's stripper (`skills/review-tone/scripts/strip_emdashes.py`) and rewrite any flagged sentence before presenting — leave code and `suggestion` blocks alone.

## Tone rules

- **The comment is the conclusion, not the proof.** It carries the point, the minimum mechanism to act on it, and the fix — nothing more. The work you did to *believe* the finding (claim verification, sibling audits, the full step-by-step causal chain, "this is the only file without the floor") is your post/drop case to the user in chat, not comment text. If a sentence exists to convince the author the bug is real rather than to help them fix it, cut it. This is the single biggest source of bloat: a thorough coalesce (SKILL.md step 4) hands you a rich justification, and the reflex is to ship it. Don't — keep the conclusion, leave the proof in chat beside it. Watch especially for framing that reflects a *sub-agent's lens* rather than the actionable point: the security agent flags a logging leak through a data-residency frame ("ships to the US-hosted Sentry"), but where the data lands doesn't change whether the author should scrub it. Keep the dimension the fix turns on (prompt text reaches Sentry), drop the one the sub-agent happened to care about (which region).
- **~3–5 sentences.** Longer usually means you're explaining your reasoning instead of making a point. The exception is a finding whose consequence is genuinely subtle (see the fail-open example below); even then, every added sentence should change what the author *does*, not just shore up your case.
- **Describe the code that's there now.** Anchor the prose to the current variables and lines — the ones you re-resolved in step 4 — not to the fix. When a finding bundles its own patch, the reflex is to open on the patch's new name ("`gradable` only checks…") as if it already exists; that's a factual slip the author will trip on. Name fix-only symbols (a new variable, a renamed function) only inside the `suggestion` block.
- **No line numbers in the comment prose.** The inline comment is already pinned to the line through the API anchor, so a `:88` in the sentence is redundant — and it rots the moment anyone rebases or edits above it. Reference code by symbol instead: the function, handler, variable, or `except` block by name ("the generic `except` in `handle_message`", not "line 119"). Symbol names survive line drift and read like a person pointing at code, not a linter citing offsets.
- **Concise.** One point per comment. No preamble, no "I noticed that…", no restating what the code already says. Don't restate the same conclusion two or three ways for emphasis ("the worst place for a false green… passes having validated nothing… grades nothing") — say it once.
- **Lead with the bottom line.** First sentence states the problem — or, in chat triage, your post/drop verdict. Then support it. Don't walk the reader through mechanism (three caches, how each is keyed, a hypothetical) before they learn what you want them to do.
- **Don't narrate the author's intent — or assign the code's rationale.** They wrote the PR; they know what it's for. Openers like "The whole point of this PR is…", "What you're doing here is…", "This PR aims to…" lecture the author about their own work and read robotic. The same goes for asserting *why* code is shaped the way it is — "this filter is the whole reason the module wraps `setup()`" tells the author their own design back at them and lands as presumptuous. State the gap without the rationale: "this doesn't pin that `before_send` reached the SDK" makes the point without claiming to know the module's purpose. Lead with what's missing or wrong. If the intent genuinely matters to the point, fold it into a clause ("the injection path these abstractions exist for has no test") instead of opening on a thesis statement.
- **Specific.** Point at the exact line and the exact consequence. "This throws if `order` is None" beats "potential null safety issue."
- **Peer, not robot.** Talk like a teammate. Drop priority codes (`P1`, `Sec-High`) and label prefixes (`blocking —`, `suggestion —`) from the comment text — say the weight in plain words instead (see "Signal weight in prose").
- **Plain words, not jargon.** Describe what the code does in concrete terms instead of reaching for security/architecture shorthand. "A new route is public unless someone adds the decorator" beats "the default is now fail-open." Terms like *fail-open / fail-closed*, *deny-by-default*, *algorithm-confusion* read robotic and can imply something literal in the code — the author goes looking for a `deny_by_default` flag that doesn't exist. Only use the term if the author would plainly recognize it, and even then say the plain version first.
- **Don't editorialize the finding's weight.** The author asked for a review; they don't need to be told that flagging is worthwhile or that a change was sneaky. Cut posture-narrating phrases — "worth a conscious call", "merits a conscious sign-off", "mostly flagging", "this is purely about X discipline", "the default quietly changed", "just flagging since". State the change and its consequence and let the prose and the question carry the weight.
- **Ask when unsure.** If the agent flagged something that depends on intent you can't see, phrase it as a question, not an assertion.
- **On judgment calls, raise the issue; don't prescribe the fix.** This is the counterpart to "Enforce, don't document" below — that rule is for correctness gaps where there's one right guard, so name it. A design or should-we-do-this finding is different: the author often has a better idea than your first one, and "this is the spot to scrub it" or "do X here" forecloses that. Surface the problem, ask if it's intended, and at most offer one direction as a parenthetical possibility ("scrubbing those keys would be one way"). Don't then add "the approach is up to you" or "your call" — that the decision is theirs is obvious and saying it is filler. The fewer words after the question mark, the more room the author has to solve it their way.
- **No AI attribution.** Never "As an AI", "Generated by", or tool-attribution footers — in the comment text or anywhere posted.
- **Earn the nits.** Batch trivial style points into a single comment, or drop them. A wall of nits buries the real issues.
- **Stand alone.** The comment is for the PR author — don't leak your review process into it. No "since it's the same file", no "the other reviewer also flagged this". Reasoning about batching, grouping, or how confident you are belongs in chat with the user, not in the posted text.
- **Never mention the sub-agents.** The author sees one reviewer — you. The fan-out into code/security/Django/GHA agents is invisible internal machinery. Phrases like "both reviewers agreed", "the reviewers concur", "both agents flagged", "all reviewers found" are confusing (the author thinks a second person they can't see is involved) and you can't use inter-agent agreement as evidence in the comment ("both reviewers agreed this isn't a security issue"). State the conclusion in your own single voice — "this isn't a security issue, just unclosed wrappers" — and drop the consensus framing entirely.
- **Enforce, don't document.** When a finding is "X should never happen" or "this case is unexpected", suggest the guard that makes it true — `raise`, `abort`, a validation check — not a code comment that merely notes the gap. A comment documents the hole; an assertion closes it. Only fall back to "leave a comment explaining why" when enforcement genuinely isn't possible.

## Signal weight in prose, not prefixes

No tag prefixes — `blocking —`, `suggestion —`, `nit —`, `question —`, `praise —` all read like a robot filled in a form. Every review comment is already a suggestion; saying so adds nothing. Convey weight the way a human reviewer does, in the sentence itself:

- **Must-fix** (correctness, security, data loss): state the failure as fact and what it breaks — "this throws when `order` is None", "`q` is interpolated straight into SQL, so this is injectable". The severity is self-evident from the consequence; you don't need to label it. If you want to be explicit that it should land before merge, say so plainly ("worth fixing before this merges") rather than stamping it.
- **Optional improvement:** phrase it as the suggestion it is — "could simplify this to…", "might be cleaner as…". The optionality is in the verb.
- **Minor / cosmetic:** lead with a soft opener — "small one:", "tiny thing —", "minor:". This is the one place a short lead-in reads naturally; "nit" is fine here if you prefer it, since reviewers say it out loud.
- **Question:** just ask it. A question mark is the only marker you need.
- **Praise:** say what's good and why, sparingly and only when you mean it.

When you present the set to the user in chat (SKILL.md step 6), you still order by value and call out which one or two matter — but that ordering and your post/drop call live in chat, not as a prefix on the comment text.

## Before / after

Agent finding:
> **[P1] Correctness** — `src/orders/api.py:42`. The variable `customer` may be `None` when `lookup_customer` returns no match, leading to a potential `AttributeError` on the subsequent attribute access `customer.email`.

Comment:
> `lookup_customer` returns `None` on a miss, so `customer.email` will throw here — guard it or return early? Worth fixing before this merges.

---

Agent finding:
> **[Sec-High]** SQL injection — user-controlled `q` is interpolated directly into the query string at `search.py:88`.

Comment:
> `q` is interpolated straight into SQL here, so this is injectable — needs a parameterized query before merge:
> ```suggestion
> cursor.execute("SELECT * FROM items WHERE name LIKE %s", [f"%{q}%"])
> ```

---

Agent finding:
> **[P3] Design** — Consider whether the retry count of 5 is appropriate; it may be excessive for this endpoint.

Comment:
> why 5 retries here? On a user-facing path that's up to ~30s of stacked backoff before we give up — intentional?

---

Agent finding:
> **[P3] Style** — `repo_uuid` parameter lacks a type annotation, unlike the sibling `hook_id: str`.

Comment:
> small one: `repo_uuid` is unannotated while `hook_id` is typed — it's a `UUID` from the auth decorator, so `repo_uuid: UUID` would match.

---

Agent finding:
> **[P2] Design** — Auth moved from a global `before_request` hook to per-route decorators. The default is now fail-open: any future route registered without an auth decorator ships publicly. Current routes are all covered, so no present exposure — this is about future-route discipline.

Comment (this is the **upper bound** on length, earned only because the consequence is subtle — a default that's fine today and bites the next person. Most comments are half this. Don't treat it as the template):
> moving auth into per-route decorators changes the default for new routes. The old `before_request` authenticated everything except health and OPTIONS, so a route was protected unless you explicitly exempted it; now a route is open unless it has a decorator. Everything here is covered, so nothing's wrong today — but the next person adding an endpoint has to remember the decorator or it ships without auth. Worth a guard in `before_request` that refuses to serve any view not marked auth-bearing, so a missing decorator fails loudly instead of serving traffic? Happy to leave it if the decorator convention is enough.

---

Agent finding:
> **[P2] Testing** — The PR adds dependency injection of `provider` and `factory` into the server constructor, but no test exercises the injected path; all tests use defaults.

Comment:
> Nothing tests the injection path — every test builds the server with defaults. A regression that dropped the injected provider, or skipped cleanup on exit, would stay green. Worth one test before merge that passes a stub provider and asserts it's actually used.

This is the intent-narration trap: the robotic version opens "The whole point of this PR is letting a deployment inject its own provider…", lecturing the author about their own change before getting to the gap. The human version opens on the gap ("Nothing tests the injection path") and folds the intent into the consequence.

---

These are the conversions to study. No prefix on any of them: the must-fix ones read as must-fix because the consequence is concrete ("will throw here", "is injectable") and they say "before merge" in words; the minor one opens with "small one:"; the design one ends on a real question and an offer to leave it. The finding's jargon ("fail-open", "future-route discipline") becomes plain English. None of them say "worth a conscious call" or "mostly flagging".

## When to use a `suggestion` block

Only when the replacement is exact and self-contained (a one-to-few line swap). For multi-file or judgment-call changes, describe the change in prose — a wrong `suggestion` block that the author one-click-commits is worse than no block.

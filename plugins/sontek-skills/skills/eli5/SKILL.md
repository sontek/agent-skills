---
name: eli5
description: Explain a topic, module, decision, or incident as if the reader knows nothing about it, then publish the explanation as a big-picture, few-words HTML Artifact. This is the default way to answer a request for a plain-language explanation. Use for "/eli5", "eli5 this", "explain like I'm 5/five", "explain this simply", "give/provide me a simple explanation", "explain how this works", "explain why we did this", "what caused this", or any other request to explain a module, decision, tradeoff, or incident in plain terms. Not for a request that explicitly wants technical depth ("deep dive", "explain in detail", "walk me through the implementation") or a task that isn't an explanation request at all (review, fix, write code).
argument-hint: '<topic, or how/why/what question about the current code or conversation>'
---

# ELI5

Turn a topic into an explanation a total newcomer could follow, then ship it
as a small, visual HTML Artifact — big pictures, few words, one idea per
screen. The hard part is not the artifact, it's getting the explanation
itself genuinely simple before any HTML gets written.

## 1. Figure out what's being explained

Two modes, same output shape:

- **Grounded** — `$ARGUMENTS` points at something in this repo or
  conversation: a module ("how does this module work"), a decision ("why
  did we make this tradeoff"), an incident ("what caused this"). Go gather
  the real facts before writing a word of explanation: read the relevant
  code, check `git log`/`git blame` for the decision's history, look for a
  postmortem or incident doc if one exists. An ELI5 built on a guess is
  worse than no ELI5 — simple and wrong is still wrong.
- **Standalone** — `$ARGUMENTS` names a general topic with nothing to
  ground it in this repo (e.g. explaining a skill a job posting asks for).
  Explain it from general knowledge. Don't invent repo-specific detail that
  isn't there.

If it's genuinely unclear which thing the user means (multiple modules or
decisions could match), ask one short question rather than guessing.

## 2. Draft the explanation as plain text first

Write the explanation as plain prose/outline before touching HTML — the
visual layer should illustrate an already-simple explanation, not disguise
a complicated one. Structure:

- **One-line hook**: the whole thing in a single plain-language sentence,
  ideally with a concrete analogy ("it's a bouncer that checks IDs before
  letting requests into the club").
- **3-5 beats**, one core idea each, picked by what's being explained:
  - *How something works*: what goes in → what happens to it → what comes
    out, as a short chain of steps.
  - *Why a tradeoff*: what we picked, what we gave up, why the giveup was
    worth it — framed as a simple weighing, not a feature list.
  - *What caused an incident*: what broke, why (root cause in one plain
    sentence), what fixed it, one line on the "in short" retro.
  - *A general topic*: what it is, why it exists, one thing it's good for,
    one thing that trips people up.
- For each beat, write out the **step sequence** it depicts, even for beats
  that aren't literally "how it works" — a tradeoff has a before/after, an
  incident has a timeline. This sequence is what step 4 draws; a beat with
  no sequence at all just gets a plain visual (a comparison, a diagram of
  the thing itself) instead of a flow.
- If a beat uses an analogy, don't just name it. Map every piece the
  reader needs, in the same sentence: not "it's a guest list" but "the
  domain publishes a list of servers allowed to send its mail, so a
  receiving server can check a new message's server against that list the
  way a doorman checks a name against the guest list." A named-but-unmapped
  analogy ("it's like a wax seal") reads as decoration, not explanation —
  if you can't finish the sentence with the real mechanism, the analogy
  isn't earning its place, cut it and just state the mechanism plainly.
- Short sentences. Define or replace jargon the moment it appears — don't
  assume the reader has any background. No hedging, no caveats stacked on
  caveats; pick the accurate simple version over the precise complicated
  one.

## 3. Run the draft through `review-tone`

Simple and concise wording is the entire point of this skill, so the plain
text draft is not done until it's clean. Invoke the **`review-tone`** skill
on the draft text (final-pass mode: apply the rules, return clean text) —
it strips filler, em-dashes, and AI-tell phrasing, and enforces
bottom-line-first, one-idea-per-sentence writing. Do this on the plain text
*before* building the artifact, not on the finished HTML — review-tone
reads prose, not markup, and fixing wording after it's embedded in HTML is
slower and easier to skip.

## 4. Build the artifact

Load the `artifact-design` skill before writing any HTML (a Claude Code
built-in skill, not part of this plugin — same for `artifact-diagramming`
below) — it's required reading for any artifact, and it's what turns "5
short paragraphs" into an actual big-picture-few-words layout (large type
for the hook, a handful of visual sections, generous whitespace, one
section in view at a time rather than a wall of text).

Load `artifact-diagramming` too, and treat it as required whenever a beat
has a step sequence (nearly every beat does — see step 2). A drawing has to
show the *mechanism*, not just gesture at the analogy:

- Draw the real nodes (sender, server, the list, the check, the outcome)
  and the real arrows between them (what gets sent, what gets compared to
  what, which branch each outcome takes). Label nodes with both the real
  name and the analogy word if one is in play, so the picture and the text
  reinforce the same mental model.
- A decision point is a decision point — draw the branch (pass/fail,
  allow/block, kept/cut) and where each path leads, don't just show one
  happy-path icon.
- **Anti-pattern**: one static icon per section (a padlock, a checkmark, a
  generic seal graphic) sitting next to prose that names the analogy. That
  illustrates a word, it doesn't show how anything works — a reader who
  covers the text should still follow the mechanism from the picture alone.
  If a beat's icon can't pass that test, replace it with an actual
  sequence/flow diagram before publishing, not after the user points it
  out.

Before publishing, run through
[references/diagram-checklist.md](references/diagram-checklist.md) — shape
bounds vs. `viewBox`, and label spacing on both straight and diagonal
connectors. These are mechanical geometry bugs a hand-authored SVG
reintroduces easily, and none of them show up until someone looks at the
rendered page.

Translate the review-tone-cleaned draft into the artifact:

- One section per beat from step 2, each with a short heading, one or two
  sentences max, and the diagram described above doing most of the
  explaining — text supports the picture, it doesn't stand in for one.
- No dense paragraphs and no code dumps — if a code reference is essential,
  name the file/function in passing text, don't paste the snippet.
- Title the artifact after the topic, not "ELI5" (e.g. "How Retry Queues
  Work", not "ELI5: Retry Queues").

Publish with the `Artifact` tool, pick a favicon emoji matching the topic,
and give the user the link.

## Output

- The published artifact link.
- One or two sentences summarizing the explanation given (not a repeat of
  the artifact's content).

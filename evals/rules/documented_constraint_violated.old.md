The honest pre-rule guidance (the "before"). No rule named the cross-region case
where a new code path violates a constraint documented elsewhere in the same file.
The reviewer had only the generic coverage instinct — read past the hunk and keep a
change consistent with the surrounding code's stated intent — with no procedure for
enumerating new branches against the enclosing block's documented constraint, no
counterweight for an in-diff rationale that excuses only one facet of the change,
and no severity floor.

- **Consistency with documented intent.** Read each affected file completely, not
  just the diff hunk — context outside the hunk is often where the real bug hides.
  Check that a change stays consistent with what the surrounding code and its
  comments say it should do, and flag inconsistencies that look unintended.

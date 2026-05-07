---
name: frontend-design
description: Design and implement distinctive, production-ready frontend interfaces with strong aesthetic direction. Use when the user asks to "design a landing page", "redesign this UI", "improve the visual design", "make this look better", "build a marketing page", "design a dashboard", "restyle this component", or wants a greenfield FE design with character — not a generic AI-default UI. Pushes Claude to commit to a single bold aesthetic (brutalist / editorial / luxury / retro-futuristic / etc.) instead of producing the same gradient-and-Inter UI every time.
---

# Frontend Design

Design and implement memorable frontend interfaces with a clear, intentional aesthetic. Output is real, working code — not mood boards. Every visual choice is rooted in purpose and context.

## Skip this skill when

- The repo has an established design system (Storybook, design tokens, component library). Match the system instead of imposing a new direction.
- The work is incremental — bug fix, minor copy change, small component tweak. The "commit to a bold direction" advice doesn't apply.
- The user asked for a specific framework / pattern (e.g., "use shadcn/ui defaults"). Follow their lead.

## Inputs to gather (or assume)

Before coding, identify:
- **Purpose & audience** — what does this UI do, and who uses it?
- **Brand & voice** — reference brands, tone, visual inspiration
- **Technical constraints** — framework, CSS strategy, accessibility, performance budget
- **Content constraints** — required copy, assets, data, features

If the user didn't provide these, ask 2–4 targeted questions, or state your assumptions briefly before coding.

## Design thinking (required)

Commit to a **single, bold aesthetic direction**. Name it. Execute it consistently. Examples:
- Brutalist / raw / utilitarian
- Editorial / magazine / typographic
- Luxury / refined / minimal
- Retro-futuristic / cyber / neon
- Art-deco / geometric / ornamental
- Handcrafted / organic / textured

**Avoid the AI-default aesthetic.** No Inter on a white background with a purple-to-pink gradient hero, no center-aligned 3-card grid below the fold, no Roboto/Arial system stacks.

Before writing code, define the system:

1. **Visual direction** — one sentence describing the vibe.
2. **Differentiator** — what should be memorable about this UI?
3. **Typography system** — display + body fonts, scale, weight, casing.
4. **Color system** — dominant, accent, neutral; declared as CSS variables.
5. **Layout strategy** — grid rhythm, spacing scale, hierarchy plan.
6. **Motion strategy** — 1–2 meaningful interaction moments (not micro-everywhere).

If the user wants code only, skip the explanation but still follow this internally.

## Implementation principles

- **Working code.** HTML/CSS/JS or framework code that runs as-is — not pseudocode.
- **Semantic & accessible.** Headings, labels, focus states, keyboard nav, `prefers-reduced-motion`.
- **Responsive.** Fluid layouts, breakpoints, responsive typography (`clamp`).
- **Tokenized styling.** CSS variables for colors, spacing, radii, shadows. Easy to tweak.
- **Modern layout.** CSS Grid + Flex. Avoid brittle absolute positioning hacks.

## Aesthetic guidelines

### Typography
- Typography defines the voice. Pick distinctive fonts.
- Avoid defaults: Inter, Roboto, Arial, system stacks.
- Use a **distinct display font** + a **refined body font**. Two is usually enough.
- Hierarchy via size, weight, spacing, casing — not just size.

### Color & theme
- Commit to a palette with a strong point of view.
- Avoid the timid, overused gradients (purple → pink on white, blue → cyan on dark).
- Use contrast intentionally; check WCAG AA for body text.

### Composition & layout
- Embrace asymmetry, scale contrast, overlap, deliberate grid breaks.
- Use negative space deliberately — or controlled density if maximalist.
- Visual rhythm and hierarchy through spacing and alignment.

### Detail & atmosphere
- Add texture or depth when it serves the concept (noise, grain, subtle patterns).
- Shadows / glows only when they earn their place.
- Unique borders, masks, clip-paths can carry distinct shapes without extra DOM.

### Motion & interaction
- Sparing but meaningful. One standout moment beats five tiny ones.
- Honor `prefers-reduced-motion`.
- Interaction should reinforce hierarchy, not compete with content.

## Anti-patterns

- Cookie-cutter hero + 3 card layouts.
- Default font choices and timid gradients.
- Unmotivated decorative elements.
- Over-flat, characterless component libraries used as the entire design.
- Animating everything because it's possible.

## Deliverables

- Full code with file names or component boundaries.
- CSS variables (or framework config) for easy customization.
- Inline SVGs or generative CSS patterns for assets when external assets aren't available.

## Quality checklist (self-validate)

- Aesthetic direction is unmistakable.
- Typography feels intentional and expressive.
- Layout and spacing are consistent and purposeful.
- Color palette feels cohesive and legible.
- Interactions enhance the experience without clutter.
- Code runs as provided and is production-ready.
- Accessibility basics: focus rings, alt text, keyboard nav, reduced motion.

**Remember:** a design is only as strong as its commitment. Choose a direction and execute it relentlessly.

## Adapted from

- [mitsuhiko/agent-stuff](https://github.com/mitsuhiko/agent-stuff/tree/main/skills/frontend-design)

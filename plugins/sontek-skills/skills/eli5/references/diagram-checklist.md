# Diagram geometry checklist

Run through this on every hand-authored SVG diagram before publishing, not
just the first one in an artifact — each new diagram is a fresh chance to
reintroduce these.

## Shape bounds

The invariant: every shape's *rendered* bounding box, not just its raw
coordinates, must sit fully inside the `viewBox`. That means accounting
for:

- Stroke width — a shape's stroke extends `stroke-width / 2` beyond its
  path on every side.
- Any ancestor `transform` — a `<g transform="translate(...)">` wrapping a
  shape shifts its real position; checking the shape's own `x`/`y` without
  applying the ancestor transform gives the wrong answer.
- The actual shape type — `rect` uses `x + width`, `y + height`;
  `polygon`/`path` uses the max/min of every point or endpoint;
  `circle`/`ellipse` uses center ± radius.

A rect that looks in-bounds by its own numbers can still be clipped if a
parent group moved it. Compute bounds after applying any transform, not
before.

Hint for the common case (no transforms, only rects and polygons): sum
each rect's `y + height` and `x + width`, and each polygon's max `x`/`y`,
and confirm the result is inside the viewBox with a few pixels of margin
for the stroke. This catches most diagrams but is a shortcut, not the
rule — a diagram using circles, paths, or nested transforms needs the
full check above.

## Label spacing

- A label centered on a short connecting segment (roughly under ~70-80px
  between the two shapes it joins) will overlap the arrowhead and the
  shape it points at. Either space the connected shapes far enough apart
  for the label's rendered width, or drop the label and put the detail
  in the figcaption instead.
- For a label on a **diagonal** line, don't eyeball an x/y that looks
  "above" the line — compute where the line actually is at that x (or
  use the line's perpendicular direction) and offset the label along
  that perpendicular by at least ~15px. A point that looks offset in
  isolation can still sit almost exactly on the line's own path once the
  slope is accounted for, which reads as text overlapping the arrow.
  This is a distinct failure from the short-segment case above and needs
  checking separately, even when segment length already looks fine.

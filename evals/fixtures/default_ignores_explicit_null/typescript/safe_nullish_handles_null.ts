// Same nullable wire field, handled correctly: nullish() accepts both null and
// undefined, and the transform coalesces either to []. No throw on explicit null.
// CLEAN — this is the fix form, not the bug.
import { z } from "zod";

const ElementSchema = z.object({ id: z.string(), kind: z.string() });

export const ResumeFrameSchema = z.object({
  threadId: z.string(),
  elements: z
    .array(ElementSchema)
    .nullish()
    .transform((v) => v ?? []),
});

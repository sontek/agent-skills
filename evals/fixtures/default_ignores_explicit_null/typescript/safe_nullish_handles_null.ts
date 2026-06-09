// Same nullable wire field: nullish() accepts both null and undefined, and the
// transform coalesces either to []. No throw on explicit null.
import { z } from "zod";

const ElementSchema = z.object({ id: z.string(), kind: z.string() });

export const ResumeFrameSchema = z.object({
  threadId: z.string(),
  elements: z
    .array(ElementSchema)
    .nullish()
    .transform((v) => v ?? []),
});

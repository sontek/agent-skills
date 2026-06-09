// Resume frame parsed from a backend that serializes the elements list as JSON
// `null` when the thread has none (the column is nullable; it is sent as null, not
// omitted). z.array(...).default([]) replaces only `undefined`, so an explicit
// `null` reaches z.array() and THROWS — the whole frame fails to parse and the
// restored conversation is dropped.
import { z } from "zod";

const ElementSchema = z.object({ id: z.string(), kind: z.string() });

export const ResumeFrameSchema = z.object({
  threadId: z.string(),
  // elements is nullable on the wire (backend sends `null`, not absent)
  elements: z.array(ElementSchema).default([]),
});

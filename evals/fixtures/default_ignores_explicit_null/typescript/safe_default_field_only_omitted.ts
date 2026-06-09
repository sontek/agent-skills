// FP / reachability guard: pageSize is a purely local, optional UI preference. The
// client form either includes it or omits it entirely — it is never sent as an
// explicit null. `.default(50)` is exactly the right tool for an absent-only field,
// so this must stay CLEAN (the validation gate's "never null, only omitted"
// exemption). A naive "flag every .default()" rule would wrongly trip here.
import { z } from "zod";

export const TablePrefsSchema = z.object({
  sortBy: z.string(),
  pageSize: z.number().default(50),
});

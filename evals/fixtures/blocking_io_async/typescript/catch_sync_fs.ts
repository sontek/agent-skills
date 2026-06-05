import { readFileSync } from "fs";

// Synchronous file read inside an async request handler blocks the Node event
// loop for every concurrent request, not just this one. Same invariant as the
// Python blocking-DB-in-async case.
export async function handleReport(req: Request): Promise<Response> {
  const template = readFileSync("/etc/report/template.html", "utf8");
  return new Response(render(template, await loadData(req)));
}

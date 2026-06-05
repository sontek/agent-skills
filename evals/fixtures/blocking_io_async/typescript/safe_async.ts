import { readFile } from "fs/promises";

export async function handleReport(req: Request): Promise<Response> {
  // Async file read yields to the event loop instead of blocking it.
  const template = await readFile("/etc/report/template.html", "utf8");
  return new Response(render(template, await loadData(req)));
}

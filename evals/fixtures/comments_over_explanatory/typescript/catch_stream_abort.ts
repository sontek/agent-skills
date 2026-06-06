function makeController(requestSignal: AbortSignal): AbortController {
  // We create a fresh AbortController instead of reusing the request's own
  // signal because the request signal is aborted by the framework as soon as
  // the response headers flush. We still need to stream the body after the
  // headers flush, so reusing the request signal would cut the stream off
  // mid-flight before the body is done.
  const controller = new AbortController();
  requestSignal.addEventListener("abort", () => controller.abort());
  return controller;
}

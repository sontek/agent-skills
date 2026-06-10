// edge/assetProxy.ts  (the diff adds the .mp4 streaming branch)
function serveAsset(key: string, body: Buffer): EdgeResponse {
  const suffix = extname(key);
  if ([".html", ".css", ".js", ".json", ".woff2"].includes(suffix)) {
    // Text assets inlined as base64 through the proxy. A redirect would change the
    // origin and break relative links / CORS, so every suffix here must stay inline.
    return { status: 200, body: body.toString("base64"), contentType: contentType(suffix) };
  }
  // .mp4 media is streamed from the CDN edge. It was never part of the inline set
  // above, so the same-origin constraint stated there does not govern it.
  if (suffix === ".mp4" && body.length > STREAM_LIMIT) {
    return { status: 302, location: cdnStreamUrl(key) };
  }
  return { status: 307, location: signedObjectUrl(key) };
}

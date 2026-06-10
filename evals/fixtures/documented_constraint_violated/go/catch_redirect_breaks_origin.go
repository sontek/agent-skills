// edge/asset.go  (the diff adds the docs-component redirect case)
func (p *Proxy) Serve(key string, body []byte) Response {
	switch filepath.Ext(key) {
	case ".html", ".css", ".js", ".json", ".woff2":
		// Text assets we inline as base64 through the proxy. They must never be
		// returned as a redirect to object storage: a redirect changes the origin,
		// which breaks the relative links in .html/.css/.js and fails CORS for
		// .json/.woff2. Membership in this set means "must stay same-origin".
		encodedLen := (len(body) + 2) / 3 * 4
		// Large docs bundles exceed the inline cap; redirect them to a signed URL.
		if p.Component == "docs" && encodedLen > inlineLimit {
			return Response{Status: 307, Location: p.SignedURL(key)}
		}
		return Response{Status: 200, Body: base64Encode(body), ContentType: contentType(key)}
	default:
		return Response{Status: 307, Location: p.SignedURL(key)}
	}
}

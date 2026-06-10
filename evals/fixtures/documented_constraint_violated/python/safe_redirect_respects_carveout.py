# edge/asset_proxy.py  (the diff adds the docs ".js" redirect branch)
def serve_asset(self, key: str, body: bytes) -> Response:
    suffix = Path(key).suffix
    if suffix in (".html", ".css", ".js", ".json", ".woff2"):
        # Served base64-inline through the proxy. A redirect to object storage
        # changes the origin, which breaks relative links in .html/.css and trips
        # CORS for .json/.woff2 — those must stay inline. The one exception is a
        # docs ".js" bundle: docs ships those as self-contained libraries with no
        # relative imports, so the origin change is safe for that suffix only.
        headers = self.security_headers()
        encoded_len = (len(body) + 2) // 3 * 4
        if self.component == "docs" and suffix == ".js" and encoded_len > INLINE_LIMIT:
            headers["location"] = self.signed_object_url(key)
            return Response(status=307, headers=headers)
        headers["content-type"] = self.content_type(key)
        return Response(status=200, body=b64encode(body), headers=headers)
    return Response(status=307, headers={"location": self.signed_object_url(key)})

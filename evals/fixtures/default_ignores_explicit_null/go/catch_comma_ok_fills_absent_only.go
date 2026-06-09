package config

// loadRetries reads an optional override from a decoded JSON object (map[string]any
// from json.Unmarshal). The comma-ok check fills the fallback only when the key is
// ABSENT. A present key with an explicit JSON null decodes to a nil value with
// ok==true, so this returns nil instead of the fallback — the nil then panics on the
// int type assertion downstream. Same absent-vs-explicit-null gap, no Zod/Pydantic.
func loadRetries(m map[string]any) any {
	val, ok := m["retries"]
	if !ok {
		return 3
	}
	return val
}

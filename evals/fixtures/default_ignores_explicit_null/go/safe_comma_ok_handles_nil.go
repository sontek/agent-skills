package config

// Same optional override: an explicit null (nil value, ok==true) falls through to
// the fallback alongside the absent case via the `|| val == nil` check, so a
// present-but-null key yields 3, not nil.
func readRetries(m map[string]any) any {
	val, ok := m["retries"]
	if !ok || val == nil {
		return 3
	}
	return val
}

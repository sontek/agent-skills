package coerce

import "time"

// Maps known runtime types to JSON-safe forms; the default returns the value
// unchanged, so an unenumerated type (time.Duration, a custom struct, a named
// int) slips through into the typed payload downstream.
func NormalizeCell(value any) any {
	switch v := value.(type) {
	case time.Time:
		return v.Format(time.RFC3339)
	case []byte:
		return string(v)
	default:
		return value // passthrough — same bug as a Python isinstance ladder
	}
}

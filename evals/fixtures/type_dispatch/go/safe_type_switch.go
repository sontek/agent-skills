package coerce

import (
	"fmt"
	"time"
)

func NormalizeCell(value any) any {
	switch v := value.(type) {
	case time.Time:
		return v.Format(time.RFC3339)
	case []byte:
		return string(v)
	case nil, bool, int, int64, float64, string:
		return value
	default:
		// Catch-all: unknown type degrades to a string, never passed through raw.
		return fmt.Sprintf("%v", value)
	}
}

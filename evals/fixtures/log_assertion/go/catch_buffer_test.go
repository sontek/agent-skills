package users

import (
	"bytes"
	"log"
	"strings"
	"testing"
)

func TestLookupMissingUserLogs(t *testing.T) {
	var buf bytes.Buffer
	log.SetOutput(&buf)
	defer log.SetOutput(nil)

	LookupUser(999)

	// Asserts on the rendered log text captured in the buffer, not on the
	// returned error. The exact same anti-pattern as caplog.text, in Go.
	if !strings.Contains(buf.String(), "user not found: 999") {
		t.Fatalf("expected log message, got %q", buf.String())
	}
}

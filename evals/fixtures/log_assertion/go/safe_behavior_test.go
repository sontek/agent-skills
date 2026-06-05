package users

import (
	"errors"
	"testing"
)

func TestLookupMissingUserReturnsError(t *testing.T) {
	// Pins behavior: the returned error wraps ErrUserNotFound. No dependence on
	// log text.
	_, err := LookupUser(999)
	if !errors.Is(err, ErrUserNotFound) {
		t.Fatalf("expected ErrUserNotFound, got %v", err)
	}
}

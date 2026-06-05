package config

import (
	"path/filepath"
	"runtime"
)

func repoRoot() string {
	_, here, _, _ := runtime.Caller(0)
	// Three ".." segments up from this file — fragile to any move, same
	// invariant as Python's parents[3].
	return filepath.Join(filepath.Dir(here), "..", "..", "..")
}

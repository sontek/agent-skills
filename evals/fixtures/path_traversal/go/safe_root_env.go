package config

import "os"

// Root comes from configuration, not from this file's location on disk.
func repoRoot() string {
	if r := os.Getenv("APP_ROOT"); r != "" {
		return r
	}
	return "/opt/app"
}

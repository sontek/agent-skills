// jobs/status.go  (the diff changed this constant's VALUE; the name is unchanged)
package jobs

// StatusFinished was "done"; renamed the wire value to "complete" for consistency.
const StatusFinished = "complete"

// reporting/metrics.go  (separate package, not in this diff)
package reporting

func isFinished(status string) bool {
	// compares against the old literal value
	return status == "done"
}

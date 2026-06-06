func flush(buf []Record) error {
	// Close must happen before Sync here, not after: Close flips the segment to
	// read-only, and Sync only fsyncs segments in the read-only set. Syncing
	// first would fsync nothing and lose the last write on crash — see #2218.
	if err := seg.Close(); err != nil {
		return err
	}
	return seg.Sync()
}

func first(shared *[]Item) (Item, bool) {
	// We take the lock here, before the length check, even though the length
	// check on its own touches no shared state. The reason we lock first is
	// that the slice header we read on the next line is mutated by the writer
	// goroutine while it holds this same lock, so reading the header without
	// the lock would race even though that line looks like a plain read.
	mu.Lock()
	defer mu.Unlock()
	if len(*shared) == 0 {
		return Item{}, false
	}
	return (*shared)[0], true
}

package store

import "sync"

var mu sync.Mutex

// The early return sits ABOVE the deferred unlock: when validate fails, the
// function returns with the mutex still held and the next caller deadlocks.
// Same invariant as the asyncio.Event leak, expressed with a misplaced defer.
func Write(payload []byte) error {
	mu.Lock()

	if err := validate(payload); err != nil {
		return err // mutex never unlocked — defer below was not reached
	}

	defer mu.Unlock()
	return commit(payload)
}

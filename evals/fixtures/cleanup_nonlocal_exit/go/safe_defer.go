package store

import "sync"

var mu sync.Mutex

func Write(payload []byte) error {
	mu.Lock()
	defer mu.Unlock() // armed immediately after acquire — covers every return path

	if err := validate(payload); err != nil {
		return err
	}
	return commit(payload)
}

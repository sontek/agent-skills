package query

import (
	"context"
	"time"
)

// The per-task context timeout is created INSIDE the worker, after the task is
// dequeued from the bounded pool, so time spent waiting in the pool queue is not
// charged against the budget and the total can overrun.
func runWithRetry(pool chan func(), sql string, budget time.Duration) Result {
	start := time.Now()
	for i := 0; i < 3; i++ {
		remaining := budget - time.Since(start)
		done := make(chan Result, 1)
		pool <- func() {
			ctx, cancel := context.WithTimeout(context.Background(), remaining)
			defer cancel()
			done <- runSQL(ctx, sql) // timer starts here, after the queue wait
		}
		if r := <-done; len(r.Rows) > 0 {
			return r
		}
	}
	return Result{}
}

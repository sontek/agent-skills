package query

import (
	"context"
	"time"
)

// The deadline context is created BEFORE the task is queued, so the pool wait
// counts against it; the worker honors the same ctx.
func runWithRetry(pool chan func(), sql string, budget time.Duration) Result {
	deadline := time.Now().Add(budget)
	for i := 0; i < 3; i++ {
		ctx, cancel := context.WithDeadline(context.Background(), deadline)
		done := make(chan Result, 1)
		pool <- func() { done <- runSQL(ctx, sql) } // ctx deadline spans queue + run
		r := <-done
		cancel()
		if len(r.Rows) > 0 {
			return r
		}
	}
	return Result{}
}

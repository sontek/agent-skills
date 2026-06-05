**Rule: Cancellation between an `asyncio.Event` acquire and its `finally`
release.** Look for an `asyncio.Event` that is `.set()` inside a `finally`
block, where an `await` sits *before* the `try:`. Grep hint:
`rg -n 'finally:|\.set\(\)|\.release\(\)'`. A `CancelledError` raised at that
`await` unwinds before the `finally` is armed, so the event is never set and
later readers waiting on it hang forever. Move the `try:` above the `await`.

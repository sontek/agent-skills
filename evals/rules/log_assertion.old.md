**Rule: No log-output assertions.** Tests that match log message text
(`assert "user not found" in caplog.text`) pin implementation, not behavior.
The log string is mutable; the behavior under test is whether the right *thing
happened* (return value, raised exception, side effect). Flag and propose
asserting on the actual outcome instead.

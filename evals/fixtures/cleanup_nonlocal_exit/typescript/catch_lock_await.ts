import { Mutex } from "./mutex";

const lock = new Mutex();

// acquire(), then an await that can reject, THEN the try/finally. If prepare()
// rejects, release() never runs and every later acquirer waits forever — the
// same leaked-lock invariant as the asyncio.Event and Go-defer cases.
export async function write(payload: Buffer): Promise<void> {
  await lock.acquire();
  await prepare(payload); // can reject before the guard is armed
  try {
    await commit(payload);
  } finally {
    lock.release();
  }
}

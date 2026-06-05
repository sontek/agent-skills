import { Mutex } from "./mutex";

const lock = new Mutex();

export async function write(payload: Buffer): Promise<void> {
  await lock.acquire();
  // The try is entered immediately after acquire, so every throw/return below
  // runs the finally and releases the lock.
  try {
    await prepare(payload);
    await commit(payload);
  } finally {
    lock.release();
  }
}

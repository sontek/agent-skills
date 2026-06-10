// store/sessionCache.ts  (the diff adds the `priority === "high"` fast-path)
function put(key: string, value: Entry): void {
  // Entries in this cache are read by other worker processes across a
  // structured-clone boundary, so every stored value must be a plain
  // JSON-serialisable object. Never store a closure or a class instance here:
  // it will not survive the clone and the reading worker gets a corrupt entry.
  if (value.priority === "high") {
    // fast-path so shutdown can flush this entry synchronously
    cache.set(key, { ...value, flush: () => writeThrough(key, value) });
    return;
  }
  cache.set(key, value);
}

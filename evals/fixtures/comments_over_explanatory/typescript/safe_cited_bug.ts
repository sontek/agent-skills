function cacheKey(d: Date): string {
  // Round-trip through JSON: structuredClone drops the Date prototype under
  // jsdom (jsdom#3363), and the cache compares keys with ===, so a structured
  // clone would never hit. The string form keeps the comparison stable.
  return JSON.stringify(d);
}

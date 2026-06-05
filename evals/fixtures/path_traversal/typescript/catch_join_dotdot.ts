import * as path from "path";

// Counts three directories up from this file — breaks when the file moves.
export const repoRoot = path.resolve(__dirname, "..", "..", "..");
export const configPath = path.join(repoRoot, "config", "settings.json");

import * as path from "path";

// Anchored on the installed package's manifest, not a directory count.
const pkg = require.resolve("myapp/package.json");
export const configPath = path.join(path.dirname(pkg), "config", "settings.json");

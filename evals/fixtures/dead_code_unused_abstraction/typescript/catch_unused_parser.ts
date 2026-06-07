// src/commandRouter.ts
export interface ParsedCommand {
  name: string;
  args: string[];
}

export class CommandRouter {
  route(raw: string): ParsedCommand {
    const [name, ...args] = raw.replace(/^\//, "").split(" ");
    return { name, args };
  }
}

// $ rg -l '\bCommandRouter\b'
// src/commandRouter.ts
// src/commandRouter.test.ts

// src/commandRouter.test.ts
test("route parses a slash command", () => {
  expect(new CommandRouter().route("/review pr 42")).toEqual({
    name: "review",
    args: ["pr", "42"],
  });
});

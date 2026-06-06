# sourceproviders/services/command_router.py
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    name: str
    args: list[str]


class CommandRouter:
    def route(self, raw: str) -> ParsedCommand:
        name, *args = raw.lstrip("/").split()
        return ParsedCommand(name=name, args=args)


# $ rg -l '\bCommandRouter\b'
# sourceproviders/services/command_router.py
# sourceproviders/tests/test_command_router.py


# sourceproviders/tests/test_command_router.py
def test_route_parses_command():
    cmd = CommandRouter().route("/review pr 42")
    assert cmd == ParsedCommand("review", ["pr", "42"])

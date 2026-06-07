# commands/review.py
# No code calls ReviewCommand.run() directly except its unit test — but the
# @register_command decorator wires it into the dispatcher's registry, and the
# bot looks it up by name at runtime. It is a live plugin entry point, not dead.
from commands.registry import register_command, Command


@register_command("review")
class ReviewCommand(Command):
    def run(self, ctx) -> str:
        return f"reviewing {ctx.target}"


def test_review_command_runs():
    assert ReviewCommand().run(ctx=_ctx(target="pr-42")) == "reviewing pr-42"

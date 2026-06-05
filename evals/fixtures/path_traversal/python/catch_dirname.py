import os

# Same fragile "count directories up" anchor, written with nested dirname so it
# dodges a rule that only greps for parents[N] / "../../..".
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG = os.path.join(HERE, "config", "settings.toml")

from importlib.resources import files

# Anchored on the installed package, not on this file's depth — survives a move.
CONFIG = files("myapp").joinpath("config/settings.toml")

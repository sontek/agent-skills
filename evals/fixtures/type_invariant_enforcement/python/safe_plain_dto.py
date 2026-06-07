# config/models.py
from dataclasses import dataclass


@dataclass
class RenderOptions:
    # A plain options bag: every field is independent and any combination is
    # legal. There is no cross-field invariant to enforce.
    dark_mode: bool = False
    font_size: int = 14
    show_line_numbers: bool = True
    wrap: bool = False

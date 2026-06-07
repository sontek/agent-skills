# scheduling/models.py
from dataclasses import dataclass
from datetime import date


@dataclass
class DateRange:
    """A span of dates. `start` is always on or before `end`."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(f"start {self.start} is after end {self.end}")

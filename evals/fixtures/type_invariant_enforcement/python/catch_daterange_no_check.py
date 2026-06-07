# scheduling/models.py
from dataclasses import dataclass
from datetime import date


@dataclass
class DateRange:
    """A span of dates. `start` is always on or before `end`."""

    start: date
    end: date


def overlaps(a: DateRange, b: DateRange) -> bool:
    return a.start <= b.end and b.start <= a.end

import functools
from datetime import datetime
from decimal import Decimal


@functools.singledispatch
def normalize_cell(value):
    return value  # permissive base case — any unregistered type passes through


@normalize_cell.register
def _(value: Decimal) -> str:
    return str(value)


@normalize_cell.register
def _(value: datetime) -> str:
    return value.isoformat()

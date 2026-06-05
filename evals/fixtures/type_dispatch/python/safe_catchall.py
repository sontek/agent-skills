from datetime import datetime
from decimal import Decimal


def normalize_cell(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    # Catch-all: an unenumerated type degrades to a string instead of slipping
    # through into the typed contract unchanged.
    return str(value)

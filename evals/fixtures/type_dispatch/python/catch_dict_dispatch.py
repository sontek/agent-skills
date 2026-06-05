from datetime import datetime
from decimal import Decimal
from uuid import UUID

# Maps DB scalar types to JSON-safe forms, then passes EVERYTHING else through
# unchanged via the dict's default. A timedelta / memoryview / Enum column
# slips through untouched and breaks the typed TableSpec union downstream —
# only for the query that selects that type. No isinstance ladder in sight.
_COERCERS = {
    Decimal: str,
    datetime: lambda v: v.isoformat(),
    UUID: str,
}


def normalize_cell(value):
    return _COERCERS.get(type(value), lambda v: v)(value)  # passthrough default

# billing/models.py
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Subscription:
    # Invariant (per the team's billing rules): a subscription is canceled IFF
    # canceled_at is set. "active" with a canceled_at, or "canceled" without one,
    # is a state we treat as impossible downstream.
    status: str  # "active" | "canceled"
    canceled_at: datetime | None = None


def is_billable(sub: Subscription) -> bool:
    return sub.status == "active"

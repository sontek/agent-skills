# billing/models.py
from pydantic import BaseModel, Field


class Account(BaseModel):
    # Invariant: balance is never negative — enforced by the library at
    # construction and on assignment via the Field constraint.
    balance: float = Field(ge=0)

    model_config = {"validate_assignment": True}

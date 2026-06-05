import pytest

from app.users import UserNotFound, lookup_user


def test_lookup_missing_user_raises():
    # Pins behavior: the function raises on a missing user. Independent of any
    # log wording.
    with pytest.raises(UserNotFound):
        lookup_user(999)

import logging
from unittest import mock

from app.users import lookup_user


def test_lookup_missing_user_logs_warning():
    logger = mock.Mock(spec=logging.Logger)

    lookup_user(999, logger=logger)

    # Asserts on the rendered log message text (via the mocked logger's call
    # args), not on behavior. Reword the log and this test breaks while the
    # behavior is unchanged.
    logger.warning.assert_called_once_with("user not found: 999")

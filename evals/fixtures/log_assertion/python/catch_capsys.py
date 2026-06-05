from app.users import lookup_user


def test_lookup_missing_user_prints(capsys):
    lookup_user(999)

    # Asserts on captured stdout text — same anti-pattern as caplog.text, a
    # different sink. Pins the message wording, not the outcome.
    out = capsys.readouterr().out
    assert "user not found: 999" in out

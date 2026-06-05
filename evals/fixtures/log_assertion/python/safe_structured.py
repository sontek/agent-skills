import logging


def test_audit_event_records_user_id(caplog):
    # Validation-gate case: structured audit logging IS the contract under test.
    # The assertion targets the structured record's FIELDS, not the rendered
    # message string, so it pins the contract, not mutable prose. Must NOT flag.
    caplog.set_level(logging.INFO)

    record_audit(user_id=999, action="lookup")

    record = next(r for r in caplog.records if r.msg == "audit.user_lookup")
    assert record.user_id == 999
    assert record.action == "lookup"

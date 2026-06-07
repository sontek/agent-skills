# sourceproviders/events.py
# This literal is genuinely CODE, not content: a small dispatch table mapping
# event types to handler callables. It is logic the function consults, it is
# short, and it does not belong in a template or data file.
def dispatch_webhook(event_type: str, payload: dict):
    handlers = {
        "pull_request": handle_pull_request,
        "push": handle_push,
        "check_run": handle_check_run,
    }
    handler = handlers.get(event_type)
    if handler is None:
        raise UnknownEvent(event_type)
    return handler(payload)

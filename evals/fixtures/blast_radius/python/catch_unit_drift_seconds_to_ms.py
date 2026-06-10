# scheduler/config.py  (the diff retuned this value)
def poll_interval():
    # Retuned for the high-frequency poller this release: value is in MILLISECONDS.
    return 500


# worker/loop.py  (separate module, imports poll_interval — NOT in this diff)
def run():
    while not shutdown:
        do_work()
        time.sleep(poll_interval())  # time.sleep takes SECONDS

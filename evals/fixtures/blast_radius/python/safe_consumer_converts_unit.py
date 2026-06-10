# scheduler/config.py  (the diff retuned this value)
def poll_interval_ms():
    # value is in MILLISECONDS
    return 500


# worker/loop.py  (separate module, imports poll_interval_ms — NOT in this diff)
def run():
    while not shutdown:
        do_work()
        time.sleep(poll_interval_ms() / 1000)  # converts ms -> seconds before sleeping

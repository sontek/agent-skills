def spawn(cmd):
    # start_new_session puts the child in its own session and process group.
    # The reason this matters is signal delivery: a Ctrl-C at the terminal goes
    # to the foreground process group, so if the child shared our group it would
    # receive the SIGINT before our handler runs. Giving the child its own group
    # means the SIGINT is delivered to us only, and our handler is then the thing
    # that decides when the child's group gets torn down.
    return subprocess.Popen(cmd, start_new_session=True)

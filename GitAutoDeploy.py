#!/usr/bin/env python

if __name__ == '__main__':
    import signal
    from GitAutoDeploy import GitAutoDeploy

    app = GitAutoDeploy()

    signal.signal(signal.SIGHUP, app.signal_handler)
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGABRT, app.signal_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    app.run()


class Lock():
    """Simple implementation of a mutex lock using the file systems. Works on
    *nix systems."""

    path = None
    lock = None

    def __init__(self, path):
        try:
            from lockfile import LockFile
        except ImportError:
            from lockfile import FileLock
            # Different naming in older versions of lockfile
            LockFile = FileLock

        self.path = path
        self.lock = LockFile(path)

    def obtain(self):
        import os
        import logging
        from lockfile import AlreadyLocked
        logger = logging.getLogger()

        try:
            self.lock.acquire(0)
            logger.debug("Successfully obtained lock: %s" % self.path)
        except AlreadyLocked:
            return False

        return True

    def release(self):
        import os
        import logging
        logger = logging.getLogger()

        if not self.has_lock():
            raise Exception("Unable to release lock that is owned by another process")

        self.lock.release()
        logger.debug("Successfully released lock: %s" % self.path)

    def has_lock(self):
        return self.lock.i_am_locking()

    def clear(self):
        import os
        import logging
        logger = logging.getLogger()

        self.lock.break_lock()
        logger.debug("Successfully cleared lock: %s" % self.path)

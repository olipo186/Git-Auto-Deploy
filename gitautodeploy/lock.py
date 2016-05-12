class Lock():
    """Simple implementation of a mutex lock using the file systems. Works on
    *nix systems."""

    path = None
    _has_lock = False

    def __init__(self, path):
        self.path = path

    def obtain(self):
        import os
        import logging
        logger = logging.getLogger()

        try:
            os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            self._has_lock = True
            logger.debug("Successfully obtained lock: %s" % self.path)
        except OSError:
            return False
        else:
            return True

    def release(self):
        import os
        import logging
        logger = logging.getLogger()

        if not self._has_lock:
            raise Exception("Unable to release lock that is owned by another process")
        try:
            os.remove(self.path)
            logger.debug("Successfully released lock: %s" % self.path)
        finally:
            self._has_lock = False

    def has_lock(self):
        return self._has_lock

    def clear(self):
        import os
        import logging
        logger = logging.getLogger()

        try:
            os.remove(self.path)
        except OSError:
            pass
        finally:
            logger.debug("Successfully cleared lock: %s" % self.path)
            self._has_lock = False
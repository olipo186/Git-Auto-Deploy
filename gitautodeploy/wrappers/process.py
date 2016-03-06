class ProcessWrapper():
    """Wraps the subprocess popen method and provides logging."""

    def __init__(self):
        pass

    @staticmethod
    def call(*popenargs, **kwargs):
        """Run command with arguments. Wait for command to complete. Sends
        output to logging module. The arguments are the same as for the Popen
        constructor."""
        
        from subprocess import Popen, PIPE
        import logging
        logger = logging.getLogger()

        kwargs['stdout'] = PIPE
        kwargs['stderr'] = PIPE

        p = Popen(*popenargs, **kwargs)
        stdout, stderr = p.communicate()

        if stdout:
            for line in stdout.strip().split("\n"):
                logger.info(line)

        if stderr:
            for line in stderr.strip().split("\n"):
                logger.error(line)

        return p.returncode
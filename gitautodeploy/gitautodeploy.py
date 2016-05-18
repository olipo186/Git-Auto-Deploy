class LogInterface(object):
    """Interface that functions as a stdout and stderr handler and directs the
    output to the logging module, which in turn will output to either console,
    file or both."""

    def __init__(self, level=None):
        import logging
        self.level = (level if level else logging.getLogger().info)

    def write(self, msg):
        for line in msg.strip().split("\n"):
            self.level(line)


class GitAutoDeploy(object):
    _instance = None
    _server = None
    _config = {}
    _port = None
    _pid = None

    def __new__(cls, *args, **kwargs):
        """Overload constructor to enable singleton access"""
        if not cls._instance:
            cls._instance = super(GitAutoDeploy, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    @staticmethod
    def debug_diagnosis(port):
        """Display information about what process is using the specified port."""
        import logging
        logger = logging.getLogger()

        pid = GitAutoDeploy.get_pid_on_port(port)
        if pid is False:
            logger.warning('Unable to determine what PID is using port %s' % port)
            return

        logger.info('Process with PID %s is using port %s' % (pid, port))
        with open("/proc/%s/cmdline" % pid) as f:
            cmdline = f.readlines()
            logger.info('Process with PID %s was started using the command: %s' % (pid, cmdline[0].replace('\x00', ' ')))

    @staticmethod
    def get_pid_on_port(port):
        """Determine what process (PID) is using a specific port."""
        import os

        with open("/proc/net/tcp", 'r') as f:
            file_content = f.readlines()[1:]

        pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
        conf_port = str(port)
        mpid = False

        for line in file_content:
            if mpid is not False:
                break

            _, laddr, _, _, _, _, _, _, _, inode = line.split()[:10]
            decport = str(int(laddr.split(':')[1], 16))

            if decport != conf_port:
                continue

            for pid in pids:
                try:
                    path = "/proc/%s/fd" % pid
                    if os.access(path, os.R_OK) is False:
                        continue

                    for fd in os.listdir(path):
                        cinode = os.readlink("/proc/%s/fd/%s" % (pid, fd))
                        minode = cinode.split(":")

                        if len(minode) == 2 and minode[1][1:-1] == inode:
                            mpid = pid

                except Exception as e:
                    pass

        return mpid

    def clone_all_repos(self):
        """Iterates over all configured repositories and clones them to their
        configured paths."""
        import os
        import re
        import logging
        from wrappers import GitWrapper
        logger = logging.getLogger()

        if not 'repositories' in self._config:
            return

        # Iterate over all configured repositories
        for repo_config in self._config['repositories']:

            # Only clone repositories with a configured path
            if 'url' not in repo_config:
                logger.critical("Repository has no configured URL")
                self.close()
                self.exit()
                return

            # Only clone repositories with a configured path
            if 'path' not in repo_config:
                logger.debug("Repository %s will not be cloned (no path configured)" % repo_config['url'])
                continue

            if os.path.isdir(repo_config['path']) and os.path.isdir(repo_config['path']+'/.git'):
                logger.debug("Repository %s already present" % repo_config['url'])
                continue

            logger.info("Repository %s not present and needs to be cloned" % repo_config['url'])

            # Clone repository
            ret = GitWrapper.clone(url=repo_config['url'], branch=repo_config['branch'], path=repo_config['path'])

            if ret == 0 and os.path.isdir(repo_config['path']):
                logger.info("Repository %s successfully cloned" % repo_config['url'])
            else:
                logger.error("Unable to clone %s branch of repository %s" % (repo_config['branch'], repo_config['url']))

    def ssh_key_scan(self):
        import re
        import logging
        from wrappers import ProcessWrapper
        logger = logging.getLogger()

        for repository in self._config['repositories']:

            url = repository['url']
            logger.info("Scanning repository: %s" % url)
            m = re.match('.*@(.*?):', url)

            if m is not None:
                port = repository['port']
                port = '' if port is None else ('-p' + port)
                ProcessWrapper().call(['ssh-keyscan -t ecdsa,rsa ' +
                                       port + ' ' +
                                       m.group(1) +
                                       ' >> ' +
                                       '$HOME/.ssh/known_hosts'], shell=True)

            else:
                logger.error('Could not find regexp match in path: %s' % url)

    def kill_conflicting_processes(self):
        """Attempt to kill any process already using the configured port."""
        import os
        import logging
        import signal
        logger = logging.getLogger()

        pid = GitAutoDeploy.get_pid_on_port(self._config['port'])

        if pid is False:
            logger.warning('No process is currently using port %s.' % self._config['port'])
            return False

        os.kill(pid, signal.SIGKILL)
        return True

    def create_pid_file(self):
        import os

        with open(self._config['pidfilepath'], 'w') as f:
            f.write(str(os.getpid()))

    def read_pid_file(self):
        with open(self._config['pidfilepath'], 'r') as f:
            return f.readlines()

    def remove_pid_file(self):
        import os
        import errno
        if 'pidfilepath' in self._config and self._config['pidfilepath']:
            try:
                os.remove(self._config['pidfilepath'])
            except OSError, e:
                if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                    raise

    def close(self):
        import sys
        import logging
        logger = logging.getLogger()
        logger.info('Goodbye')
        self.remove_pid_file()
        if 'intercept-stdout' in self._config and self._config['intercept-stdout']:
            sys.stdout = self._default_stdout
            sys.stderr = self._default_stderr

    def exit(self):
        import sys
        self.close()
        sys.exit(0)

    @staticmethod
    def create_daemon():
        import os

        try:
            # Spawn first child. Returns 0 in the child and pid in the parent.
            pid = os.fork()
        except OSError, e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        # First child
        if pid == 0:
            os.setsid()

            try:
                # Spawn second child
                pid = os.fork()
                
            except OSError, e:
                raise Exception("%s [%d]" % (e.strerror, e.errno))

            if pid == 0:
                os.umask(0)
            else:
                # Kill first child
                os._exit(0)
        else:
            # Kill parent of first child
            os._exit(0)

        return 0

    def setup(self, config):
        """Setup an instance of GAD based on the provided config object."""
        import sys
        from BaseHTTPServer import HTTPServer
        import socket
        import os
        import logging
        from lock import Lock
        from httpserver import WebhookRequestHandler

        # Attatch config values to this instance
        self._config = config

        # Set up logging
        logger = logging.getLogger()
        logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

        # Enable console output?
        if ('quiet' in self._config and self._config['quiet']) or ('daemon-mode' in self._config and self._config['daemon-mode']):
            logger.addHandler(logging.NullHandler())
        else:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)

            # Check if a stream handler is already present (will be if GAD is started by test script)
            handler_present = False
            for handler in logger.handlers:
                if isinstance(handler, type(consoleHandler)):
                    handler_present = True
                    break

            if not handler_present:
                logger.addHandler(consoleHandler)

        # Set logging level
        if 'log-level' in self._config:
            level = logging.getLevelName(self._config['log-level'])
            logger.setLevel(level)

        if 'logfilepath' in self._config and self._config['logfilepath']:
            # Translate any ~ in the path into /home/<user>
            fileHandler = logging.FileHandler(self._config['logfilepath'])
            fileHandler.setFormatter(logFormatter)
            logger.addHandler(fileHandler)

        if 'ssh-keygen' in self._config and self._config['ssh-keygen']:
            logger.info('Scanning repository hosts for ssh keys...')
            self.ssh_key_scan()

        if 'force' in self._config and self._config['force']:
            logger.info('Attempting to kill any other process currently occupying port %s' % self._config['port'])
            self.kill_conflicting_processes()

        # Clone all repos once initially
        self.clone_all_repos()

        # Set default stdout and stderr to our logging interface (that writes
        # to file and console depending on user preference)
        if 'intercept-stdout' in self._config and self._config['intercept-stdout']:
            self._default_stdout = sys.stdout
            self._default_stderr = sys.stderr
            sys.stdout = LogInterface(logger.info)
            sys.stderr = LogInterface(logger.error)

        if 'daemon-mode' in self._config and self._config['daemon-mode']:
            logger.info('Starting Git Auto Deploy in daemon mode')
            GitAutoDeploy.create_daemon()
        else:
            logger.info('Git Auto Deploy started')

        self._pid = os.getpid()
        self.create_pid_file()

        # Clear any existing lock files, with no regard to possible ongoing processes
        for repo_config in self._config['repositories']:

            # Do we have a physical repository?
            if 'path' in repo_config:
                Lock(os.path.join(repo_config['path'], 'status_running')).clear()
                Lock(os.path.join(repo_config['path'], 'status_waiting')).clear()

        try:
            WebhookRequestHandler._config = self._config
            self._server = HTTPServer((self._config['host'],
                                       self._config['port']),
                                      WebhookRequestHandler)

            if 'ssl' in self._config and self._config['ssl']:
                import ssl
                logger.info("enabling ssl")
                self._server.socket = ssl.wrap_socket(self._server.socket,
                                                      certfile=os.path.expanduser(self._config['ssl-pem']),
                                                      server_side=True)
            sa = self._server.socket.getsockname()
            logger.info("Listening on %s port %s", sa[0], sa[1])

            # Actual port bound to (nessecary when OS picks randomly free port)
            self._port = sa[1]

        except socket.error, e:

            logger.critical("Error on socket: %s" % e)
            GitAutoDeploy.debug_diagnosis(self._config['port'])

            sys.exit(1)

    def serve_forever(self):
        """Start listening for incoming requests."""
        import sys
        import socket
        import logging

        # Set up logging
        logger = logging.getLogger()

        try:
            self._server.serve_forever()

        except socket.error, e:
            logger.critical("Error on socket: %s" % e)
            sys.exit(1)
        
        except KeyboardInterrupt, e:
            logger.info('Requested close by keyboard interrupt signal')
            self.stop()
            self.exit()

    def handle_request(self):
        """Start listening for incoming requests."""
        import sys
        import socket
        import logging

        # Set up logging
        logger = logging.getLogger()

        try:
            self._server.handle_request()

        except socket.error, e:
            logger.critical("Error on socket: %s" % e)
            sys.exit(1)
        
        except KeyboardInterrupt, e:
            logger.info('Requested close by keyboard interrupt signal')
            self.stop()
            self.exit()

    def stop(self):
        if self._server is None:
            return
        self._server.socket.close()

    def signal_handler(self, signum, frame):
        import logging
        logger = logging.getLogger()
        self.stop()

        if signum == 1:
            self.setup(self._config)
            self.serve_forever()
            return

        elif signum == 2:
            logger.info('Requested close by keyboard interrupt signal')

        elif signum == 6:
            logger.info('Requested close by SIGABRT (process abort signal). Code 6.')

        self.exit()

def main():
    import signal
    from gitautodeploy import GitAutoDeploy
    from cli.config import get_config_defaults, get_config_from_environment, get_config_from_argv, find_config_file, get_config_from_file, get_repo_config_from_environment, init_config
    import sys
    import os

    app = GitAutoDeploy()

    signal.signal(signal.SIGHUP, app.signal_handler)
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGABRT, app.signal_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    config = get_config_defaults()

    # Get config values from environment variables and commadn line arguments
    environment_config = get_config_from_environment()
    argv_config = get_config_from_argv(sys.argv[1:])

    # Merge config values
    config.update(environment_config)
    config.update(argv_config)

    # Config file path provided?
    if 'config' in config and config['config']:
        config_file_path = os.path.realpath(config['config'])

    else:

        # Directories to scan for config files
        target_directories = [
            os.getcwd(),  # cwd
            os.path.dirname(os.path.realpath(__file__))  # script path
        ]

        config_file_path = find_config_file(target_directories)

    # Config file path provided or found?
    if config_file_path:
        file_config = get_config_from_file(config_file_path)
        config.update(file_config)

    # Extend config data with any repository defined by environment variables
    repo_config = get_repo_config_from_environment()

    if repo_config:

        if not 'repositories' in config:
            config['repositories'] = []

        config['repositories'].append(repo_config)

    # Initialize config by expanding with missing values
    init_config(config)

    app.setup(config)
    app.serve_forever()

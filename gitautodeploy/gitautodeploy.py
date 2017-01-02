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
    _http_server = None
    #_ws_server = None
    _config = {}
    _port = None
    _pid = None
    _event_store = None
    _default_stdout = None
    _default_stderr = None
    _startup_event = None

    def __new__(cls, *args, **kwargs):
        """Overload constructor to enable singleton access"""
        if not cls._instance:
            cls._instance = super(GitAutoDeploy, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        from events import EventStore, StartupEvent

        # Setup an event store instance that can keep a global record of events
        self._event_store = EventStore()
        self._event_store.register_observer(self)

        # Create a startup event that can hold status and any error messages from the startup process
        self._startup_event = StartupEvent()
        self._event_store.register_action(self._startup_event)

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
                self.exit()
                return

            # Only clone repositories with a configured path
            if 'path' not in repo_config:
                logger.debug("Repository %s will not be cloned (no path configured)" % repo_config['url'])
                continue

            if os.path.isdir(repo_config['path']) and os.path.isdir(repo_config['path']+'/.git'):
                GitWrapper.init(repo_config)
            else:
                GitWrapper.clone(repo_config)

    def ssh_key_scan(self):
        import re
        import logging
        from wrappers import ProcessWrapper
        logger = logging.getLogger()

        for repository in self._config['repositories']:
            
            if not 'url' in repository:
                continue

            logger.info("Scanning repository: %s" % repository['url'])
            m = re.match('[^\@]+\@([^\:\/]+)(:(\d+))?', repository['url'])

            if m is not None:
                host = m.group(1)
                port = m.group(3)
                port_arg = '' if port is None else ('-p %s ' % port)
                cmd = 'ssh-keyscan %s%s >> $HOME/.ssh/known_hosts' % (port_arg, host)
                ProcessWrapper().call([cmd], shell=True)

            else:
                logger.error('Could not find regexp match in path: %s' % repository['url'])

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

    def update(self, *args, **kwargs):
        pass

    def setup(self, config):
        """Setup an instance of GAD based on the provided config object."""
        import sys
        from BaseHTTPServer import HTTPServer
        import socket
        import os
        import logging
        from lock import Lock
        from httpserver import WebhookRequestHandlerFactory

        # This solves https://github.com/olipo186/Git-Auto-Deploy/issues/118
        try:
            from logging import NullHandler
        except ImportError:
            from logging import Handler

            class NullHandler(Handler):
                def emit(self, record):
                    pass

        # Attatch config values to this instance
        self._config = config

        # Set up logging
        logger = logging.getLogger()
        logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

        # Enable console output?
        if ('quiet' in self._config and self._config['quiet']) or ('daemon-mode' in self._config and self._config['daemon-mode']):
            logger.addHandler(NullHandler())
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

        if 'ssh-keyscan' in self._config and self._config['ssh-keyscan']:
            self._startup_event.log_info('Scanning repository hosts for ssh keys...')
            self.ssh_key_scan()

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
            self._startup_event.log_info('Starting Git Auto Deploy in daemon mode')
            GitAutoDeploy.create_daemon()
        else:
            self._startup_event.log_info('Git Auto Deploy started')

        self._pid = os.getpid()
        self.create_pid_file()

        # Clear any existing lock files, with no regard to possible ongoing processes
        for repo_config in self._config['repositories']:

            # Do we have a physical repository?
            if 'path' in repo_config:
                Lock(os.path.join(repo_config['path'], 'status_running')).clear()
                Lock(os.path.join(repo_config['path'], 'status_waiting')).clear()

        try:

            # Create web hook request handler class
            WebhookRequestHandler = WebhookRequestHandlerFactory(self._config, self._event_store)

            # Create HTTP server
            self._http_server = HTTPServer((self._config['host'],
                                       self._config['port']),
                                      WebhookRequestHandler)

            #try:
            #    from SimpleWebSocketServer import SimpleWebSocketServer
            #    from wsserver import WebSocketClientHandler

            #    # Create web socket server
            #    self._ws_server = SimpleWebSocketServer(self._config['ws-host'], self._config['ws-port'], WebSocketClientHandler)

            #except ImportError as e:
            #    self._startup_event.log_error("Unable to start web socket server due to lack of compability. python => 2.7.9 is required.")

            # Setup SSL for HTTP server
            if 'ssl' in self._config and self._config['ssl']:
                import ssl
                logger.info("enabling ssl")
                self._http_server.socket = ssl.wrap_socket(self._http_server.socket,
                                                      certfile=os.path.expanduser(self._config['ssl-pem']),
                                                      server_side=True)
            sa = self._http_server.socket.getsockname()
            self._startup_event.log_info("Listening on %s port %s" % (sa[0], sa[1]))
            self._startup_event.address = sa[0]
            self._startup_event.port = sa[1]
            self._startup_event.notify()

            # Actual port bound to (nessecary when OS picks randomly free port)
            self._port = sa[1]

        except socket.error, e:
            self._startup_event.log_critical("Error on socket: %s" % e)
            sys.exit(1)

    def serve_http(self):
        import sys
        import socket
        import logging
        import os
        from events import SystemEvent

        try:
            self._http_server.serve_forever()

        except socket.error, e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_critical("Error on socket: %s" % e)
            sys.exit(1)
        
        except KeyboardInterrupt, e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_info('Requested close by keyboard interrupt signal')
            self.stop()
            self.exit()

        pass

    #def serve_ws(self):
    #    if not self._ws_server:
    #        return
    #    self._ws_server.serveforever()

    def serve_forever(self):
        """Start listening for incoming requests."""
        import sys
        import socket
        import logging
        import os
        from events import SystemEvent
        import threading

        # Add script dir to sys path, allowing us to import sub modules even after changing cwd
        sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))

        # Set CWD to public www folder. This makes the http server serve files from the wwwroot directory.
        wwwroot = os.path.join(os.path.dirname(os.path.realpath(__file__)), "wwwroot")
        os.chdir(wwwroot)

        t1 = threading.Thread(target=self.serve_http)
        #t1.daemon = True
        t1.start()


        #t2 = threading.Thread(target=self.serve_ws)
        #t1.daemon = True
        #t2.start()

        # Wait for thread to finish without blocking main thread
        while t1.isAlive:
            t1.join(5)

        # Wait for thread to finish without blocking main thread
        #while t2.isAlive:
        #    t2.join(5)


    def handle_request(self):
        """Start listening for incoming requests."""
        import sys
        import socket
        from events import SystemEvent

        try:
            self._http_server.handle_request()

        except socket.error, e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_critical("Error on socket: %s" % e)
            sys.exit(1)
        
        except KeyboardInterrupt, e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_info('Requested close by keyboard interrupt signal')
            self.stop()
            self.exit()

    def signal_handler(self, signum, frame):
        from events import SystemEvent
        self.stop()

        event = SystemEvent()
        self._event_store.register_action(event)

        # Reload configuration on SIGHUP events (conventional for daemon processes)
        if signum == 1:
            self.setup(self._config)
            self.serve_forever()
            return

        # Keyboard interrupt signal
        elif signum == 2:
            event.log_info('Recieved keyboard interrupt signal (%s) from the OS, shutting down.' % signum)

        else:
            event.log_info('Recieved signal (%s) from the OS, shutting down.' % signum)

        self.exit()

    def stop(self):
        """Stop all running TCP servers (HTTP and web socket servers)"""

        # Stop HTTP server if running
        if self._http_server is not None:

            # Shut down the underlying TCP server
            self._http_server.shutdown()
            # Close the socket
            self._http_server.socket.close()

        # Stop web socket server if running
        #if self._ws_server is not None:
        #    self._ws_server.close()

    def exit(self):
        import sys
        import logging
        logger = logging.getLogger()
        logger.info('Goodbye')

        # Delete PID file
        self.remove_pid_file()

        # Restore stdin and stdout
        if 'intercept-stdout' in self._config and self._config['intercept-stdout']:
            sys.stdout = self._default_stdout
            sys.stderr = self._default_stderr

        sys.exit(0)

def main():
    import signal
    from gitautodeploy import GitAutoDeploy
    from cli.config import get_config_defaults, get_config_from_environment, get_config_from_argv, find_config_file, get_config_from_file, get_repo_config_from_environment, init_config
    import sys
    import os

    app = GitAutoDeploy()

    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, app.signal_handler)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, app.signal_handler)
    if hasattr(signal, 'SIGABRT'):
        signal.signal(signal.SIGABRT, app.signal_handler)
    if hasattr(signal, 'SIGPIPE') and hasattr(signal, 'SIG_IGN'):
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

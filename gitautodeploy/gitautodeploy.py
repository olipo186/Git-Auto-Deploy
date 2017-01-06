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

    def flush(self):
        pass

from .wsserver import WebSocketClientHandlerFactory
from .httpserver import WebhookRequestHandlerFactory

class GitAutoDeploy(object):
    _instance = None
    _http_server = None
    _https_server = None
    _https_server_unwrapped_socket = None
    _config = {}
    _server_status = {}
    _pid = None
    _event_store = None
    _default_stdout = None
    _default_stderr = None
    _startup_event = None
    _ws_clients = []

    def __new__(cls, *args, **kwargs):
        """Overload constructor to enable singleton access"""
        if not cls._instance:
            cls._instance = super(GitAutoDeploy, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        from .events import EventStore, StartupEvent

        # Setup an event store instance that can keep a global record of events
        self._event_store = EventStore()
        self._event_store.register_observer(self)

        # Create a startup event that can hold status and any error messages
        # from the startup process
        self._startup_event = StartupEvent()
        self._event_store.register_action(self._startup_event)

    def clone_all_repos(self):
        """Iterates over all configured repositories and clones them to their
        configured paths."""
        import os
        import re
        import logging
        from .wrappers import GitWrapper
        logger = logging.getLogger()

        if 'repositories' not in self._config:
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
        from .wrappers import ProcessWrapper
        logger = logging.getLogger()

        for repository in self._config['repositories']:

            if 'url' not in repository:
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

        with open(self._config['pid-file'], 'w') as f:
            f.write(str(os.getpid()))

    def read_pid_file(self):
        with open(self._config['pid-file'], 'r') as f:
            return f.readlines()

    def remove_pid_file(self):
        import os
        import errno
        if 'pid-file' in self._config and self._config['pid-file']:
            try:
                os.remove(self._config['pid-file'])
            except OSError as e:
                # errno.ENOENT = no such file or directory
                if e.errno != errno.ENOENT:
                    raise

    @staticmethod
    def create_daemon():
        import os

        try:
            # Spawn first child. Returns 0 in the child and pid in the parent.
            pid = os.fork()
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        # First child
        if pid == 0:
            os.setsid()

            try:
                # Spawn second child
                pid = os.fork()

            except OSError as e:
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
        import json
        data = json.dumps(kwargs).encode('utf-8')
        for client in self._ws_clients:
            client.sendMessage(data)

    def setup(self, config):
        """Setup an instance of GAD based on the provided config object."""
        import sys
        import socket
        import os
        import logging
        from .lock import Lock

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

        if 'log-file' in self._config and self._config['log-file']:
            # Translate any ~ in the path into /home/<user>
            fileHandler = logging.FileHandler(self._config['log-file'])
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

        self._pid = os.getpid()
        self.create_pid_file()

        # Clear any existing lock files, with no regard to possible ongoing processes
        for repo_config in self._config['repositories']:

            # Do we have a physical repository?
            if 'path' in repo_config:
                Lock(os.path.join(repo_config['path'], 'status_running')).clear()
                Lock(os.path.join(repo_config['path'], 'status_waiting')).clear()

        #if 'daemon-mode' not in self._config or not self._config['daemon-mode']:
        #    self._startup_event.log_info('Git Auto Deploy started')

    def serve_http(self):
        """Starts a HTTP server that listens for webhook requests and serves the web ui."""
        import sys
        import socket
        import os
        from .events import SystemEvent

        try:
            from BaseHTTPServer import HTTPServer
        except ImportError as e:
            from http.server import HTTPServer

        if not self._config['http-enabled']:
            return

        # Setup
        try:

            # Create web hook request handler class
            WebhookRequestHandler = WebhookRequestHandlerFactory(self._config, self._event_store, self._server_status, is_https=False)

            # Create HTTP server
            self._http_server = HTTPServer((self._config['http-host'],
                                       self._config['http-port']),
                                      WebhookRequestHandler)

            # Setup SSL for HTTP server
            sa = self._http_server.socket.getsockname()
            self._server_status['http-uri'] = "http://%s:%s" % (self._config['http-host'], self._config['http-port'])

            self._startup_event.log_info("Listening for connections on %s" % self._server_status['http-uri'])
            self._startup_event.http_address = sa[0]
            self._startup_event.http_port = sa[1]
            self._startup_event.set_http_started(True)

        except socket.error as e:
            self._startup_event.log_critical("Unable to start HTTP server: %s" % e)
            return

        # Run forever
        try:
            self._http_server.serve_forever()

        except socket.error as e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_critical("Error on socket: %s" % e)
            sys.exit(1)

        except KeyboardInterrupt as e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_info('Requested close by keyboard interrupt signal')
            self.stop()
            self.exit()

        event = SystemEvent()
        self._event_store.register_action(event)
        event.log_info('HTTP server did quit')

    def serve_https(self):
        """Starts a HTTPS server that listens for webhook requests and serves the web ui."""
        import sys
        import socket
        import os
        import ssl
        from .events import SystemEvent

        try:
            from BaseHTTPServer import HTTPServer
        except ImportError as e:
            from http.server import HTTPServer

        if not self._config['https-enabled']:
            return

        if not os.path.isfile(self._config['ssl-cert']):
            self._startup_event.log_critical("Unable to activate SSL: File does not exist: %s" % self._config['ssl-cert'])
            return

        # Setup
        try:

            # Create web hook request handler class
            WebhookRequestHandler = WebhookRequestHandlerFactory(self._config, self._event_store, self._server_status, is_https=True)

            # Create HTTP server
            self._https_server = HTTPServer((self._config['https-host'],
                                       self._config['https-port']),
                                      WebhookRequestHandler)

            # Setup SSL for HTTP server
            self._https_server_unwrapped_socket = self._https_server.socket
            self._https_server.socket = ssl.wrap_socket(self._https_server.socket,
                                                keyfile=self._config['ssl-key'],
                                                certfile=self._config['ssl-cert'],
                                                server_side=True)

            sa = self._https_server.socket.getsockname()
            self._server_status['https-uri'] = "https://%s:%s" % (self._config['https-host'], self._config['https-port'])

            self._startup_event.log_info("Listening for connections on %s" % self._server_status['https-uri'])
            self._startup_event.http_address = sa[0]
            self._startup_event.http_port = sa[1]
            self._startup_event.set_http_started(True)

        except socket.error as e:
            self._startup_event.log_critical("Unable to start HTTPS server: %s" % e)
            return

        # Run forever
        try:
            self._https_server.serve_forever()

        except socket.error as e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_critical("Error on socket: %s" % e)
            sys.exit(1)

        except KeyboardInterrupt as e:
            event = SystemEvent()
            self._event_store.register_action(event)
            event.log_info('Requested close by keyboard interrupt signal')
            self.stop()
            self.exit()

        event = SystemEvent()
        self._event_store.register_action(event)
        event.log_info('HTTPS server did quit')

    def serve_wss(self):
        """Start a web socket server over SSL, used by the web UI to get notifications about updates."""
        import os

        # Start a web socket server if the web UI is enabled
        if not self._config['web-ui-enabled']:
            return

        if not self._config['wss-enabled']:
            return

        if not os.path.isfile(self._config['ssl-cert']):
            self._startup_event.log_critical("Unable to activate SSL: File does not exist: %s" % self._config['ssl-cert'])
            return

        try:
            import os
            from autobahn.websocket import WebSocketServerProtocol, WebSocketServerFactory
            from twisted.internet import reactor, ssl
            from twisted.internet.error import BindError

            # Create a WebSocketClientHandler instance
            WebSocketClientHandler = WebSocketClientHandlerFactory(self._config, self._ws_clients, self._event_store)

            uri = u"ws://%s:%s" % (self._config['wss-host'], self._config['wss-port'])
            factory = WebSocketServerFactory(uri)
            factory.protocol = WebSocketClientHandler
            # factory.setProtocolOptions(maxConnections=2)

            # note to self: if using putChild, the child must be bytes...
            if self._config['ssl-key'] and self._config['ssl-cert']:
                contextFactory = ssl.DefaultOpenSSLContextFactory(privateKeyFileName=self._config['ssl-key'], certificateFileName=self._config['ssl-cert'])
            else:
                contextFactory = ssl.DefaultOpenSSLContextFactory(privateKeyFileName=self._config['ssl-cert'], certificateFileName=self._config['ssl-cert'])


            self._ws_server_port = reactor.listenSSL(self._config['wss-port'], factory, contextFactory)
            # self._ws_server_port = reactor.listenTCP(self._config['wss-port'], factory)

            self._server_status['wss-uri'] = "wss://%s:%s" % (self._config['wss-host'], self._config['wss-port'])

            self._startup_event.log_info("Listening for connections on %s" % self._server_status['wss-uri'])
            self._startup_event.ws_address = self._config['wss-host']
            self._startup_event.ws_port = self._config['wss-port']
            self._startup_event.set_ws_started(True)

            # Serve forever (until reactor.stop())
            reactor.run(installSignalHandlers=False)

        except BindError as e:
            self._startup_event.log_critical("Unable to start web socket server: %s" % e)

        except ImportError:
            self._startup_event.log_error("Unable to start web socket server due to missing dependency.")

        event = SystemEvent()
        self._event_store.register_action(event)
        event.log_info('WSS server did quit')

    def serve_forever(self):
        """Start HTTP and web socket servers."""
        import sys
        import socket
        import logging
        import os
        from .events import SystemEvent
        import threading

        try:
            from autobahn.websocket import WebSocketServerProtocol, WebSocketServerFactory
            from twisted.internet import reactor

            # Given that the nessecary dependencies are present, notify the
            # event that we expect the web socket server to be started
            self._startup_event.ws_started = False
        except ImportError:
            pass

        # Notify the event that we expect the http server to be started
        self._startup_event.http_started = False

        # Add script dir to sys path, allowing us to import sub modules even after changing cwd
        sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))

        # Set CWD to public www folder. This makes the http server serve files from the wwwroot directory.
        wwwroot = os.path.join(os.path.dirname(os.path.realpath(__file__)), "wwwroot")
        os.chdir(wwwroot)

        threads = [
            # HTTP server
            threading.Thread(target=self.serve_http),

            # HTTPS server
            threading.Thread(target=self.serve_https),

            # Web socket SSL server
            threading.Thread(target=self.serve_wss)
        ]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for each thread to finish
        for thread in threads:

            # Wait for thread to finish without blocking main thread
            while thread.is_alive():
                thread.join(5)

    def signal_handler(self, signum, frame):
        from .events import SystemEvent
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

        # Stop HTTPS server if running
        if self._https_server is not None:

            # Shut down the underlying TCP server
            self._https_server.shutdown()

            # Close the socket
            self._https_server.socket.close()

        if self._https_server_unwrapped_socket is not None:

            self._https_server_unwrapped_socket.close()

        # Stop web socket server if running
        try:
            from twisted.internet import reactor
            reactor.callFromThread(reactor.stop)
        except ImportError:
            pass

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


def main():
    import signal
    from gitautodeploy import GitAutoDeploy
    from cli.config import get_config_defaults, get_config_from_environment
    from cli.config import get_config_from_argv, find_config_file
    from cli.config import get_config_from_file, get_repo_config_from_environment
    from cli.config import init_config, get_config_file_path, rename_legacy_attribute_names
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

    # Get default config values
    config = get_config_defaults()

    # Get config values from environment variables and commadn line arguments
    environment_config = get_config_from_environment()
    argv_config = get_config_from_argv(sys.argv[1:])

    # Merge config values from environment variables
    config.update(environment_config)

    search_target = os.path.dirname(os.path.realpath(__file__))
    config_file_path = get_config_file_path(environment_config, argv_config, search_target)

    # Config file path provided or found?
    if config_file_path:
        file_config = get_config_from_file(config_file_path)

        # Merge config values from config file (overrides environment variables)
        config.update(file_config)

    # Merge config value from command line (overrides environment variables and config file)
    config.update(argv_config)

    # Rename legacy config option names
    config = rename_legacy_attribute_names(config)

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

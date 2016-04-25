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
    _config = None

    def __new__(cls, *args, **kwargs):
        """Overload constructor to enable Singleton access"""
        if not cls._instance:
            cls._instance = super(GitAutoDeploy, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    @staticmethod
    def debug_diagnosis(port):
        import logging
        logger = logging.getLogger()

        pid = GitAutoDeploy.get_pid_on_port(port)
        if pid is False:
            logger.warning('I don\'t know the number of pid that is using my configured port')
            return

        logger.info('Process with pid number %s is using port %s' % (pid, port))
        with open("/proc/%s/cmdline" % pid) as f:
            cmdline = f.readlines()
            logger.info('cmdline ->', cmdline[0].replace('\x00', ' '))

    @staticmethod
    def get_pid_on_port(port):
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

    def find_config_file_path(self):
        """Attempt to find a config file in cwd and script path."""

        import os
        import re
        import logging
        logger = logging.getLogger()

        # Look for a custom config file if no path is provided as argument
        target_directories = [
            os.path.dirname(os.path.realpath(__file__)),  # Script path
        ]

        # Add current CWD if not identical to script path
        if not os.getcwd() in target_directories:
            target_directories.append(os.getcwd())
        
        target_directories.reverse()

        # Look for a *conf.json or *config.json
        for dir in target_directories:
            if not os.access(dir, os.R_OK):
                continue
            for item in os.listdir(dir):
                if re.match(r".*conf(ig)?\.json$", item):
                    path = os.path.realpath(os.path.join(dir, item))
                    logger.info("Using '%s' as config" % path)
                    return path

        return
    
    def read_json_file(self, file_path):
        import json
        import logging
        import re
        logger = logging.getLogger()
        
        try:
            json_string = open(file_path).read()

        except Exception as e:
            logger.critical("Could not load %s file\n" % file_path)
            raise e

        try:
            # Remove commens from JSON (makes sample config options easier)
            regex = r'\s*(#|\/{2}).*$'
            regex_inline = r'(:?(?:\s)*([A-Za-z\d\.{}]*)|((?<=\").*\"),?)(?:\s)*(((#|(\/{2})).*)|)$'
            lines = json_string.split('\n')

            for index, line in enumerate(lines):
                if re.search(regex, line):
                    if re.search(r'^' + regex, line, re.IGNORECASE):
                        lines[index] = ""
                    elif re.search(regex_inline, line):
                        lines[index] = re.sub(regex_inline, r'\1', line)
                        
            data = json.loads('\n'.join(lines))

        except Exception as e:
            logger.critical("%s file is not valid JSON\n" % file_path)
            raise e

        return data

    def read_repo_config_from_environment(self, config_data):
        """Look for repository config in any defined environment variables. If
        found, import to main config."""
        import logging
        import os

        if 'GAD_REPO_URL' not in os.environ:
            return config_data

        logger = logging.getLogger()

        repo_config = {
            'url': os.environ['GAD_REPO_URL']
        }
        
        logger.info("Added configuration for '%s' found in environment variables" % os.environ['GAD_REPO_URL'])

        if 'GAD_REPO_BRANCH' in os.environ:
            repo_config['branch'] = os.environ['GAD_REPO_BRANCH']

        if 'GAD_REPO_REMOTE' in os.environ:
            repo_config['remote'] = os.environ['GAD_REPO_REMOTE']

        if 'GAD_REPO_PATH' in os.environ:
            repo_config['path'] = os.environ['GAD_REPO_PATH']

        if 'GAD_REPO_DEPLOY' in os.environ:
            repo_config['deploy'] = os.environ['GAD_REPO_DEPLOY']

        if not 'repositories' in config_data:
            config_data['repositories'] = []

        config_data['repositories'].append(repo_config)

        return config_data

    def init_config(self, config_data):
        import os
        import re
        import logging
        logger = logging.getLogger()
        
        self._config = config_data

        # Translate any ~ in the path into /home/<user>
        if 'pidfilepath' in self._config:
            self._config['pidfilepath'] = os.path.expanduser(self._config['pidfilepath'])

        if 'repositories' not in self._config:
            self._config['repositories'] = []

        for repo_config in self._config['repositories']:

            # Setup branch if missing
            if 'branch' not in repo_config:
                repo_config['branch'] = "master"

            # Setup remote if missing
            if 'remote' not in repo_config:
                repo_config['remote'] = "origin"

            # Setup deploy commands list if not present
            if 'deploy_commands' not in repo_config:
                repo_config['deploy_commands'] = []

            # Check if any global pre deploy commands is specified
            if 'global_deploy' in self._config and len(self._config['global_deploy'][0]) is not 0:
                repo_config['deploy_commands'].insert(0, self._config['global_deploy'][0])

            # Check if any repo specific deploy command is specified
            if 'deploy' in repo_config:
                repo_config['deploy_commands'].append(repo_config['deploy'])

            # Check if any global post deploy command is specified
            if 'global_deploy' in self._config and len(self._config['global_deploy'][1]) is not 0:
                repo_config['deploy_commands'].append(self._config['global_deploy'][1])

            # If a Bitbucket repository is configured using the https:// URL, a username is usually
            # specified in the beginning of the URL. To be able to compare configured Bitbucket
            # repositories with incoming web hook events, this username needs to be stripped away in a
            # copy of the URL.
            if 'url' in repo_config and 'bitbucket_username' not in repo_config:
                regexp = re.search(r"^(https?://)([^@]+)@(bitbucket\.org/)(.+)$", repo_config['url'])
                if regexp:
                    repo_config['url_without_usernme'] = regexp.group(1) + regexp.group(3) + regexp.group(4)

            # Translate any ~ in the path into /home/<user>
            if 'path' in repo_config:
                repo_config['path'] = os.path.expanduser(repo_config['path'])

        return self._config

    def clone_all_repos(self):
        """Iterates over all configured repositories and clones them to their
        configured paths."""
        import os
        import re
        import logging
        from wrappers import GitWrapper
        logger = logging.getLogger()

        # Iterate over all configured repositories
        for repo_config in self._config['repositories']:
            
            # Only clone repositories with a configured path
            if 'path' not in repo_config:
                logger.info("Repository %s will not be cloned (no path configured)" % repo_config['url'])
                continue
            
            if os.path.isdir(repo_config['path']) and os.path.isdir(repo_config['path']+'/.git'):
                logger.info("Repository %s already present" % repo_config['url'])
                continue

            # Clone repository
            GitWrapper.clone(url=repo_config['url'], branch=repo_config['branch'], path=repo_config['path'])
            
            if os.path.isdir(repo_config['path']):
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
        import os
        import logging
        logger = logging.getLogger()

        pid = GitAutoDeploy.get_pid_on_port(self._config['port'])

        if pid is False:
            logger.error('[KILLER MODE] I don\'t know the number of pid ' +
                         'that is using my configured port\n[KILLER MODE] ' +
                         'Maybe no one? Please, use --force option carefully')
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
        os.remove(self._config['pidfilepath'])

    def exit(self):
        import sys
        import logging
        logger = logging.getLogger()
        logger.info('Goodbye')
        self.remove_pid_file()
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

    def run(self):
        import sys
        from BaseHTTPServer import HTTPServer
        import socket
        import os
        import logging
        import argparse
        from lock import Lock
        from httpserver import WebhookRequestHandler

        # Attempt to retrieve default config values from environment variables
        default_quiet_value = 'GAD_QUIET' in os.environ or False
        default_daemon_mode_value = 'GAD_DAEMON_MODE' in os.environ or False
        default_config_value = 'GAD_CONFIG' in os.environ and os.environ['GAD_CONFIG'] or None
        default_ssh_keygen_value = 'GAD_SSH_KEYGEN' in os.environ or False
        default_force_value = 'GAD_FORCE' in os.environ or False
        default_use_ssl = 'GAD_SSL' in os.environ or False
        default_ssl_pem_file_path = 'GAD_SSL_PEM_FILE' in os.environ and os.environ['GAD_SSL_PEM_FILE'] or '~/.gitautodeploy.pem'
        default_pid_file_value = 'GAD_PID_FILE' in os.environ and os.environ['GAD_PID_FILE'] or '~/.gitautodeploy.pid'
        default_log_file_value = 'GAD_LOG_FILE' in os.environ and os.environ['GAD_LOG_FILE'] or None
        default_host_value = 'GAD_HOST' in os.environ and os.environ['GAD_HOST'] or '0.0.0.0'
        default_port_value = 'GAD_PORT' in os.environ and int(os.environ['GAD_PORT']) or 8001

        parser = argparse.ArgumentParser()

        parser.add_argument("-d", "--daemon-mode",
                            help="run in background (daemon mode)",
                            default=default_daemon_mode_value,
                            action="store_true")

        parser.add_argument("-q", "--quiet",
                            help="supress console output",
                            default=default_quiet_value,
                            action="store_true")

        parser.add_argument("-c", "--config",
                            help="custom configuration file",
                            default=default_config_value,
                            type=str)

        parser.add_argument("--ssh-keygen",
                            help="scan repository hosts for ssh keys",
                            default=default_ssh_keygen_value,
                            action="store_true")

        parser.add_argument("--force",
                            help="kill any process using the configured port",
                            default=default_force_value,
                            action="store_true")

        parser.add_argument("--pid-file",
                            help="specify a custom pid file",
                            #default=default_pid_file_value,
                            type=str)

        parser.add_argument("--log-file",
                            help="specify a log file",
                            #default=default_log_file_value,
                            type=str)

        parser.add_argument("--host",
                            help="address to bind to",
                            #default=default_host_value,
                            type=str)

        parser.add_argument("--port",
                            help="port to bind to",
                            #default=default_port_value,
                            type=int)

        parser.add_argument("--ssl",
                            help="use ssl",
                            default=default_use_ssl,
                            action="store_true")

        parser.add_argument("--ssl-pem",
                            help="path to ssl pem file",
                            default=default_ssl_pem_file_path,
                            type=str)

        args = parser.parse_args()

        # Set up logging
        logger = logging.getLogger()
        logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

        # Enable console output?
        if args.quiet:
            logger.addHandler(logging.NullHandler())
        else:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            logger.addHandler(consoleHandler)

        # All logs are recording
        logger.setLevel(logging.NOTSET)

        # Look for log file path provided in argument
        config_file_path = None
        if args.config:
            config_file_path = os.path.realpath(args.config)
            logger.info('Using custom configuration file \'%s\'' % config_file_path)

        # Try to find a config file on the file system
        if not config_file_path:
            config_file_path = self.find_config_file_path()

        # Read config data from json file
        if config_file_path:
            config_data = self.read_json_file(config_file_path)
        else:
            logger.info('No configuration file found or specified. Using default values.')
            config_data = {}

        # Pid file config
        if args.pid_file:
            config_data['pidfilepath'] = args.pid_file
        elif not 'pidfilepath' in config_data:
            config_data['pidfilepath'] = default_pid_file_value

        # Log file config
        if args.log_file:
            config_data['logfilepath'] = args.log_file
        elif not 'logfilepath' in config_data:
            config_data['logfilepath'] = default_log_file_value

        # Port config
        if args.port:
            config_data['port'] = args.port
        elif not 'port' in config_data:
            config_data['port'] = default_port_value

        # Host config
        if args.host:
            config_data['host'] = args.host
        elif not 'host' in config_data:
            config_data['host'] = default_host_value

        # Extend config data with any repository defined by environment variables
        config_data = self.read_repo_config_from_environment(config_data)

        # Initialize config using config file data
        self.init_config(config_data)

        if 'logfilepath' in self._config and self._config['logfilepath']:
            # Translate any ~ in the path into /home/<user>
            log_file_path = os.path.expanduser(self._config['logfilepath'])
            fileHandler = logging.FileHandler(log_file_path)
            fileHandler.setFormatter(logFormatter)
            logger.addHandler(fileHandler)

        if args.ssh_keygen:
            logger.info('Scanning repository hosts for ssh keys...')
            self.ssh_key_scan()

        if args.force:
            logger.info('Attempting to kill any other process currently occupying port %s' % self._config['port'])
            self.kill_conflicting_processes()

        # Clone all repos once initially
        self.clone_all_repos()

        # Set default stdout and stderr to our logging interface (that writes
        # to file and console depending on user preference)
        sys.stdout = LogInterface(logger.info)
        sys.stderr = LogInterface(logger.error)

        if args.daemon_mode:
            logger.info('Starting Git Auto Deploy in daemon mode')
            GitAutoDeploy.create_daemon()
        else:
            logger.info('Git Auto Deploy started')

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
            if args.ssl:
                import ssl
                logger.info("enabling ssl")
                self._server.socket = ssl.wrap_socket(self._server.socket,
                                                      certfile=os.path.expanduser(args.ssl_pem),
                                                      server_side=True)
            sa = self._server.socket.getsockname()
            logger.info("Listening on %s port %s", sa[0], sa[1])
            self._server.serve_forever()

        except socket.error, e:

            if not args.daemon_mode:
                logger.critical("Error on socket: %s" % e)
                GitAutoDeploy.debug_diagnosis(self._config['port'])

            sys.exit(1)

    def stop(self):
        if self._server is not None:
            self._server.socket.close()

    def signal_handler(self, signum, frame):
        import logging
        logger = logging.getLogger()
        self.stop()

        if signum == 1:
            self.run()
            return

        elif signum == 2:
            logger.info('Requested close by keyboard interrupt signal')

        elif signum == 6:
            logger.info('Requested close by SIGABRT (process abort signal). Code 6.')

        self.exit()


def main():
    import signal
    from gitautodeploy import GitAutoDeploy

    app = GitAutoDeploy()

    signal.signal(signal.SIGHUP, app.signal_handler)
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGABRT, app.signal_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    app.run()
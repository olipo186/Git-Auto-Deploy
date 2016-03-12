#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler


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
            logger.info("Successfully obtained lock: %s" % self.path)
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
            logger.info("Successfully released lock: %s" % self.path)
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
            logger.info("Successfully cleared lock: %s" % self.path)
            self._has_lock = False


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


class GitWrapper():
    """Wraps the git client. Currently uses git through shell command
    invocations."""

    def __init__(self):
        pass

    @staticmethod
    def pull(repo_config):
        """Pulls the latest version of the repo from the git server"""
        import logging
        
        logger = logging.getLogger()
        logger.info("Post push request received")

        # Only pull if there is actually a local copy of the repository
        if 'path' not in repo_config:
            logger.info('No local repository path configured, no pull will occure')
            return 0
        
        logger.info('Updating ' + repo_config['path'])

#        cmd = 'cd "' + repo_config['path'] + '"' \
        cmd =   'unset GIT_DIR ' + \
                '&& git fetch ' + repo_config['remote'] + \
                '&& git reset --hard ' + repo_config['remote'] + '/' + repo_config['branch'] + ' ' + \
                '&& git submodule init ' + \
                '&& git submodule update'

        # '&& git update-index --refresh ' +\
        res = ProcessWrapper().call([cmd], cwd=repo_config['path'], shell=True)
        logger.info('Pull result: ' + str(res))

        return int(res)

    @staticmethod
    def clone(url, branch, path):
        ProcessWrapper().call(['git clone --recursive ' + url + ' -b ' + branch + ' ' + path], shell=True)

    @staticmethod
    def deploy(repo_config):
        """Executes any supplied post-pull deploy command"""
        from subprocess import call
        import logging
        logger = logging.getLogger()

        if 'path' in repo_config:
            path = repo_config['path']

        logger.info('Executing deploy command(s)')
        
        # Use repository path as default cwd when executing deploy commands
        cwd = (repo_config['path'] if 'path' in repo_config else None)

        for cmd in repo_config['deploy_commands']:
            ProcessWrapper().call([cmd], cwd=cwd, shell=True)


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Extends the BaseHTTPRequestHandler class and handles the incoming
    HTTP requests."""

    def do_POST(self):
        """Invoked on incoming POST requests"""
        from threading import Timer

        # Extract repository URL(s) from incoming request body
        repo_urls, ref, action = self.get_repo_params_from_request()
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        # Wait one second before we do git pull (why?)
        Timer(1.0, GitAutoDeploy.process_repo_urls, (repo_urls,
                                                     ref,
                                                     action)).start()

    def log_message(self, format, *args):
        """Overloads the default message logging method to allow messages to
        go through our custom logger instead."""
        import logging
        logger = logging.getLogger()
        logger.info("%s - - [%s] %s\n" % (self.client_address[0],
                                          self.log_date_time_string(),
                                          format%args))

    def get_repo_params_from_request(self):
        """Parses the incoming request and extracts all possible URLs to the
        repository in question. Since repos can have both ssh://, git:// and
        https:// URIs, and we don't know which of them is specified in the
        config, we need to collect and compare them all."""
        import json
        import logging

        logger = logging.getLogger()

        content_type = self.headers.getheader('content-type')
        length = int(self.headers.getheader('content-length'))
        body = self.rfile.read(length)

        data = json.loads(body)

        repo_urls = []
        ref = ""
        action = ""

        gitlab_event = self.headers.getheader('X-Gitlab-Event')
        github_event = self.headers.getheader('X-GitHub-Event')
        user_agent = self.headers.getheader('User-Agent')

        # Assume GitLab if the X-Gitlab-Event HTTP header is set
        if gitlab_event:

            logger.info("Received '%s' event from GitLab" % gitlab_event)

            if 'repository' not in data:
                logger.error("ERROR - Unable to recognize data format")
                return repo_urls, ref or "master", action

            # One repository may posses multiple URLs for different protocols
            for k in ['url', 'git_http_url', 'git_ssh_url']:
                if k in data['repository']:
                    repo_urls.append(data['repository'][k])

            # extract the branch
            if 'ref' in data:
                ref = data['ref']

            # set the action
            if 'object_kind' in data:
                action = data['object_kind']

        # Assume GitHub if the X-GitHub-Event HTTP header is set
        elif github_event:

            logger.info("Received '%s' event from GitHub" % github_event)

            if 'repository' not in data:
                logger.error("ERROR - Unable to recognize data format")
                return repo_urls, ref or "master", action

            # One repository may posses multiple URLs for different protocols
            for k in ['url', 'git_url', 'clone_url', 'ssh_url']:
                if k in data['repository']:
                    repo_urls.append(data['repository'][k])

            if 'pull_request' in data:
                if 'base' in data['pull_request']:
                    if 'ref' in data['pull_request']['base']:
                        ref = data['pull_request']['base']['ref']
                        logger.info("Pull request to branch '%s' was fired" % ref)
            elif 'ref' in data:
                ref = data['ref']
                logger.info("Push to branch '%s' was fired" % ref)

            if 'action' in data:
                action = data['action']
                logger.info("Action '%s' was fired" % action)

        # Assume BitBucket if the User-Agent HTTP header is set to 'Bitbucket-Webhooks/2.0' (or something similar)
        elif user_agent and user_agent.lower().find('bitbucket') != -1:

            logger.info("Received event from BitBucket")

            if 'repository' not in data:
                logger.error("ERROR - Unable to recognize data format")
                return repo_urls, ref or "master", action

            # One repository may posses multiple URLs for different protocols
            for k in ['url', 'git_url', 'clone_url', 'ssh_url']:
                if k in data['repository']:
                    repo_urls.append(data['repository'][k])

            if 'full_name' in data['repository']:
                repo_urls.append('git@bitbucket.org:%s.git' % data['repository']['full_name'])

                # Add a simplified version of the bitbucket HTTPS URL - without the username@bitbucket.com part. This is
                # needed since the configured repositories might be configured using a different username.
                repo_urls.append('https://bitbucket.org/%s.git' % (data['repository']['full_name']))

        # Special Case for Gitlab CI
        elif content_type == "application/json" and "build_status" in data:

            logger.info('Received event from Gitlab CI')

            if 'push_data' not in data:
                logger.error("ERROR - Unable to recognize data format")
                return repo_urls, ref or "master", action

            # Only add repositories if the build is successful. Ignore it in other case.
            if data['build_status'] == "success":
                for k in ['url', 'git_http_url', 'git_ssh_url']:
                    if k in data['push_data']['repository']:
                        repo_urls.append(data['push_data']['repository'][k])
            else:
                logger.warning("Gitlab CI build '%d' has status '%s'. Not pull will be done" % (
                    data['build_id'], data['build_status']))

        # Try to find the repository urls and add them as long as the content type is set to JSON at least.
        # This handles old GitLab requests and Gogs requests for example.
        elif content_type == "application/json":

            logger.info("Received event from unknown origin. Assume generic data format.")

            if 'repository' not in data:
                logger.error("ERROR - Unable to recognize data format")
                return repo_urls, ref or "master", action

            # One repository may posses multiple URLs for different protocols
            for k in ['url', 'git_http_url', 'git_ssh_url', 'http_url', 'ssh_url']:
                if k in data['repository']:
                    repo_urls.append(data['repository'][k])
        else:
            logger.error("ERROR - Unable to recognize request origin. Don't know how to handle the request.")

        logger.info("Event details - ref: %s; action: %s" % (ref or "master", action))
        return repo_urls, ref or "master", action


# Used to describe when a filter does not match a request
class FilterMatchError(Exception): pass


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

    @staticmethod
    def process_repo_urls(urls, ref, action):
        import os
        import time
        import logging
        logger = logging.getLogger()

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = GitAutoDeploy().get_matching_repo_configs(urls)

        if len(repo_configs) == 0:
            logger.warning('Unable to find any of the repository URLs in the config: %s' % ', '.join(urls))
            return

        # Process each matching repository
        for repo_config in repo_configs:

            try:
                # Verify that all filters matches the request if specified
                if 'filters' in repo_config:
                    for filter in repo_config['filters']:
                        if 'type' in filter and filter['type'] == 'pull-request-filter':
                            if filter['ref'] == ref and filter['action'] == action:
                                continue
                            raise FilterMatchError()
                        else:
                            if 'action' in filter and filter['action'] != action:
                                raise FilterMatchError()
                            if 'ref' in filter and filter['ref'] != ref:
                                raise FilterMatchError()
                            
            except FilterMatchError as e:
                continue
            
            
            # In case there is no path configured for the repository, no pull will
            # be made.
            if not 'path' in repo_config:
                GitWrapper.deploy(repo_config)
                continue
            
            running_lock = Lock(os.path.join(repo_config['path'], 'status_running'))
            waiting_lock = Lock(os.path.join(repo_config['path'], 'status_waiting'))
            try:

                # Attempt to obtain the status_running lock
                while not running_lock.obtain():

                    # If we're unable, try once to obtain the status_waiting lock
                    if not waiting_lock.has_lock() and not waiting_lock.obtain():
                        logger.error("Unable to obtain the status_running lock nor the status_waiting lock. Another process is " +
                                        "already waiting, so we'll ignore the request.")

                        # If we're unable to obtain the waiting lock, ignore the request
                        break

                    # Keep on attempting to obtain the status_running lock until we succeed
                    time.sleep(5)

                n = 4
                while 0 < n and 0 != GitWrapper.pull(repo_config):
                    n -= 1

                if 0 < n:
                    GitWrapper.deploy(repo_config)

            except Exception as e:
                logger.error('Error during \'pull\' or \'deploy\' operation on path: %s' % repo_config['path'])
                logger.error(e)

            finally:

                # Release the lock if it's ours
                if running_lock.has_lock():
                    running_lock.release()

                # Release the lock if it's ours
                if waiting_lock.has_lock():
                    waiting_lock.release()

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
            for item in os.listdir(dir):
                if re.match(r"conf(ig)?\.json$", item):
                    path = os.path.realpath(os.path.join(dir, item))
                    logger.info("Using '%s' as config" % path)
                    return path

        return './GitAutoDeploy.conf.json'

    def read_json_file(self, file_path):
        import json
        import logging
        logger = logging.getLogger()
        
        try:
            json_string = open(file_path).read()

        except Exception as e:
            logger.critical("Could not load %s file\n" % file_path)
            raise e

        try:
            data = json.loads(json_string)

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
        
        logger.info("Added configuration for '%s' found environment variables" % os.environ['GAD_REPO_URL'])

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
            if len(self._config['global_deploy'][0]) is not 0:
                repo_config['deploy_commands'].insert(0, self._config['global_deploy'][0])

            # Check if any repo specific deploy command is specified
            if 'deploy' in repo_config:
                repo_config['deploy_commands'].append(repo_config['deploy'])

            # Check if any global post deploy command is specified
            if len(self._config['global_deploy'][1]) is not 0:
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


    def get_matching_repo_configs(self, urls):
        """Iterates over the various repo URLs provided as argument (git://,
        ssh:// and https:// for the repo) and compare them to any repo URL
        specified in the config"""

        configs = []
        for url in urls:
            for repo_config in self._config['repositories']:
                if repo_config in configs:
                    continue
                if repo_config['url'] == url:
                    configs.append(repo_config)
                elif 'url_without_usernme' in repo_config and repo_config['url_without_usernme'] == url:
                    configs.append(repo_config)

        return configs

    def ssh_key_scan(self):
        import re
        import logging
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
        logger.info('\nGoodbye')
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
                os.chdir('/')
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

        # Attempt to retrieve default config values from environment variables
        default_quiet_value = 'GAD_QUIET' in os.environ
        default_daemon_mode_value = 'GAD_DAEMON_MODE' in os.environ
        default_config_value = 'GAD_CONFIG' in os.environ and os.environ['GAD_CONFIG']
        default_ssh_keygen_value = 'GAD_SSH_KEYGEN' in os.environ
        default_force_value = 'GAD_FORCE' in os.environ
        default_pid_file_value = 'GAD_PID_FILE' in os.environ and os.environ['GAD_PID_FILE']
        default_log_file_value = 'GAD_LOG_FILE' in os.environ and os.environ['GAD_LOG_FILE']
        default_host_value = 'GAD_HOST' in os.environ and os.environ['GAD_HOST']
        default_port_value = 'GAD_PORT' in os.environ and int(os.environ['GAD_PORT'])

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
                            default=default_pid_file_value,
                            type=str)

        parser.add_argument("--log-file",
                            help="specify a log file",
                            default=default_log_file_value,
                            type=str)

        parser.add_argument("--host",
                            help="address to bind to",
                            default=default_host_value,
                            type=str)

        parser.add_argument("--port",
                            help="port to bind to",
                            default=default_port_value,
                            type=int)

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
        config_data = self.read_json_file(config_file_path)

        # Configuration options coming from environment or command line will
        # override those coming from config file
        if args.pid_file:
            config_data['pidfilepath'] = args.pid_file

        if args.log_file:
            config_data['logfilepath'] = args.log_file

        if args.host:
            config_data['host'] = args.host

        if args.port:
            config_data['port'] = args.port

        # Extend config data with any repository defined by environment variables
        config_data = self.read_repo_config_from_environment(config_data)

        # Initialize config using config file data
        self.init_config(config_data)

        # Translate any ~ in the path into /home/<user>
        if 'logfilepath' in self._config:
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
            self._server = HTTPServer((self._config['host'],
                                       self._config['port']),
                                      WebhookRequestHandler)
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
            logger.info('\nRequested close by keyboard interrupt signal')

        elif signum == 6:
            logger.info('Requested close by SIGABRT (process abort signal). Code 6.')

        self.exit()


if __name__ == '__main__':
    import signal

    app = GitAutoDeploy()

    signal.signal(signal.SIGHUP, app.signal_handler)
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGABRT, app.signal_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    app.run()

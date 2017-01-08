def get_config_defaults():
    """Get the default configuration values."""

    config = {}

    # Supress console output
    config['quiet'] = False

    # Run in daemon mode
    config['daemon-mode'] = False

    # File containing additional config options
    config['config'] = None

    # File to store a copy of the console output
    config['log-file'] = None

    # File to store the process id (pid)
    config['pid-file'] = '~/.gitautodeploy.pid'

    # HTTP server options
    config['http-enabled'] = True
    config['http-host'] = '0.0.0.0'
    config['http-port'] = 8001

    # HTTPS server options
    config['https-enabled'] = True
    config['https-host'] = '0.0.0.0'
    config['https-port'] = 8002

    # Web socket server options (used by web UI for real time updates)
    config['wss-enabled'] = False  # Disabled by default until authentication is in place
    config['wss-host'] = '0.0.0.0'
    config['wss-port'] = 8003

    # TLS/SSL cert (necessary for HTTPS and web socket server to work)
    config['ssl-key'] = None  # If specified, holds the private key
    config['ssl-cert'] = '~/cert.pem'  # Holds the public key or both the private and public keys

    # Web user interface options
    config['web-ui-enabled'] = False  # Disabled by default until authentication is in place
    config['web-ui-username'] = None
    config['web-ui-password'] = None
    config['web-ui-whitelist'] = ['127.0.0.1']
    config['web-ui-require-https'] = True
    config['web-ui-auth-enabled'] = True
    config['web-ui-prevent-root'] = True

    # Record all log levels by default
    config['log-level'] = 'NOTSET'

    # Other options
    config['intercept-stdout'] = True
    config['ssh-keyscan'] = False
    config['allow-root-user'] = False

    # Include details with deploy command return codes in HTTP response. Causes
    # to await any git pull or deploy command actions before it sends the
    # response.
    config['detailed-response'] = False

    # Log incoming webhook requests in a way they can be used as test cases
    config['log-test-case'] = False
    config['log-test-case-dir'] = None

    return config


def rename_legacy_attribute_names(config):
    import logging
    logger = logging.getLogger()

    rewrite_map = {
        'ssl': 'https-enabled',
        'ssl-pem-file': 'ssl-cert',
        'host': 'http-host',
        'port': 'http-port',
        'pidfilepath': 'pid-file',
        'logfilepath': 'log-file'
    }

    for item in rewrite_map.items():
        old_name, new_name = item
        if old_name in config:
            config[new_name] = config[old_name]
            del config[old_name]
            print("Config option '%s' is deprecated. Please use '%s' instead." % (old_name, new_name))

    return config


def get_config_from_environment():
    """Get configuration values provided as environment variables."""
    import os

    config = {}

    if 'GAD_QUIET' in os.environ:
        config['quiet'] = True

    if 'GAD_DAEMON_MODE' in os.environ:
        config['daemon-mode'] = True

    if 'GAD_CONFIG' in os.environ:
        config['config'] = os.environ['GAD_CONFIG']

    if 'GAD_SSH_KEYSCAN' in os.environ:
        config['ssh-keyscan'] = True

    if 'GAD_SSL_KEY' in os.environ:
        config['ssl-key'] = os.environ['GAD_SSL_KEY']

    if 'GAD_SSL_CERT' in os.environ:
        config['ssl-cert'] = os.environ['GAD_SSL_CERT']

    if 'GAD_PID_FILE' in os.environ:
        config['pid-file'] = os.environ['GAD_PID_FILE']

    if 'GAD_LOG_FILE' in os.environ:
        config['log-file'] = os.environ['GAD_LOG_FILE']

    if 'GAD_HOST' in os.environ:
        config['http-host'] = os.environ['GAD_HOST']

    if 'GAD_HTTP_HOST' in os.environ:
        config['http-host'] = os.environ['GAD_HTTP_HOST']

    if 'GAD_HTTPS_HOST' in os.environ:
        config['https-host'] = os.environ['GAD_HTTPS_HOST']

    if 'GAD_PORT' in os.environ:
        config['http-port'] = int(os.environ['GAD_PORT'])

    if 'GAD_HTTP_PORT' in os.environ:
        config['http-port'] = int(os.environ['GAD_HTTP_PORT'])

    if 'GAD_HTTPS_PORT' in os.environ:
        config['https-port'] = int(os.environ['GAD_HTTPS_PORT'])

    return config


def get_config_from_argv(argv):
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--daemon-mode",
                        help="run in background (daemon mode)",
                        dest="daemon-mode",
                        default=None,
                        action="store_true")

    parser.add_argument("-q", "--quiet",
                        help="supress console output",
                        dest="quiet",
                        default=None,
                        action="store_true")

    parser.add_argument("-c", "--config",
                        help="custom configuration file",
                        dest="config",
                        type=str)

    parser.add_argument("--ssh-keyscan",
                        help="scan repository hosts for ssh keys",
                        dest="ssh-keyscan",
                        default=None,
                        action="store_true")

    parser.add_argument("--pid-file",
                        help="specify a custom pid file",
                        dest="pid-file",
                        type=str)

    parser.add_argument("--log-file",
                        help="specify a log file",
                        dest="log-file",
                        type=str)

    parser.add_argument("--log-level",
                        help="specify log level",
                        dest="log-level",
                        type=str)

    parser.add_argument("--host",
                        help="address to bind http server to",
                        dest="http-host",
                        type=str)

    #parser.add_argument("--http-host",
    #                    help="address to bind http server to",
    #                    dest="http-host",
    #                    type=str)

    #parser.add_argument("--https-host",
    #                    help="address to bind https server to",
    #                    dest="https-host",
    #                    type=str)

    parser.add_argument("--port",
                        help="port to bind http server to",
                        dest="http-port",
                        type=int)

    #parser.add_argument("--http-port",
    #                    help="port to bind http server to",
    #                    dest="http-port",
    #                    type=int)

    #parser.add_argument("--https-port",
    #                    help="port to bind http server to",
    #                    dest="https-port",
    #                    type=int)

    parser.add_argument("--ws-port",
                        help="port to bind web socket server to",
                        dest="web-ui-web-socket-port",
                        type=int)

    parser.add_argument("--ssl",
                        help="enable https",
                        dest="https-enabled",
                        default=None,
                        action="store_true")

    parser.add_argument("--ssl-key",
                        help="path to ssl key file",
                        dest="ssl-key",
                        type=str)

    parser.add_argument("--ssl-cert",
                        help="path to ssl cert file",
                        dest="ssl-cert",
                        type=str)

    parser.add_argument("--allow-root-user",
                        help="allow running as root user",
                        dest="allow-root-user",
                        default=None,
                        action="store_true")


    config = vars(parser.parse_args(argv))

    # Delete entries for unprovided arguments
    del_keys = []
    for key in config:
        if config[key] is None:
            del_keys.append(key)

    for key in del_keys:
        del config[key]

    return config


def find_config_file(target_directories=None):
    """Attempt to find a path to a config file. Provided paths are scanned
    for *.conf(ig)?.json files."""
    import os
    import re
    import logging
    logger = logging.getLogger()

    if not target_directories:
        return

    # Remove duplicates
    target_directories = list(set(target_directories))

    # Look for a *conf.json or *config.json
    for dir in target_directories:

        if not os.access(dir, os.R_OK):
            continue

        for item in os.listdir(dir):
            if re.match(r".*conf(ig)?\.json$", item):
                path = os.path.realpath(os.path.join(dir, item))
                logger.info("Using '%s' as config" % path)
                return path


def get_config_from_file(path):
    """Get configuration values from config file."""
    import logging
    import os
    logger = logging.getLogger()

    config_file_path = os.path.realpath(path)
    logger.info('Using custom configuration file \'%s\'' % config_file_path)

    # Read config data from json file
    if config_file_path:
        config_data = read_json_file(config_file_path)
    else:
        logger.info('No configuration file found or specified. Using default values.')
        config_data = {}

    return config_data


def read_json_file(file_path):
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


def init_config(config):
    """Initialize config by filling out missing values etc."""

    import os
    import re
    import logging
    logger = logging.getLogger()

    # Translate any ~ in the path into /home/<user>
    if 'pid-file' in config and config['pid-file']:
        config['pid-file'] = os.path.expanduser(config['pid-file'])

    if 'log-file' in config and config['log-file']:
        config['log-file'] = os.path.expanduser(config['log-file'])

    if 'ssl-cert' in config and config['ssl-cert']:
        config['ssl-cert'] = os.path.expanduser(config['ssl-cert'])

    if 'ssl-key' in config and config['ssl-key']:
        config['ssl-key'] = os.path.expanduser(config['ssl-key'])

    if 'repositories' not in config:
        config['repositories'] = []

    for repo_config in config['repositories']:

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
        if 'global_deploy' in config and len(config['global_deploy']) > 0 and len(config['global_deploy'][0]) is not 0:
            repo_config['deploy_commands'].insert(0, config['global_deploy'][0])

        # Check if any repo specific deploy command is specified
        if 'deploy' in repo_config:
            repo_config['deploy_commands'].append(repo_config['deploy'])

        # Check if any global post deploy command is specified
        if 'global_deploy' in config and len(config['global_deploy']) > 1 and len(config['global_deploy'][1]) is not 0:
            repo_config['deploy_commands'].append(config['global_deploy'][1])

        # If a repository is configured with embedded credentials, we create an alternate URL
        # without these credentials that cen be used when comparing the URL with URLs referenced
        # in incoming web hook requests.
        if 'url' in repo_config:
            regexp = re.search(r"^(https?://)([^@]+)@(.+)$", repo_config['url'])
            if regexp:
                repo_config['url_without_usernme'] = regexp.group(1) + regexp.group(3)

        # Translate any ~ in the path into /home/<user>
        if 'path' in repo_config:
            repo_config['path'] = os.path.expanduser(repo_config['path'])

        # Support for legacy config format
        if 'filters' in repo_config:
            repo_config['payload-filter'] = repo_config['filters']
            del repo_config['filters']

        if 'payload-filter' not in repo_config:
            repo_config['payload-filter'] = []

        if 'header-filter' not in repo_config:
            repo_config['header-filter'] = {}

        # Rewrite some legacy filter config syntax
        for filter in repo_config['payload-filter']:

            # Legacy config syntax?
            if ('kind' in filter and filter['kind'] == 'pull-request-handler') or ('type' in filter and filter['type'] == 'pull-request-filter'):

                # Reset legacy values
                filter['kind'] = None
                filter['type'] = None

                if 'ref' in filter:
                    filter['pull_request.base.ref'] = filter['ref']
                    filter['ref'] = None

                filter['pull_request'] = True

    return config


def get_repo_config_from_environment():
    """Look for repository config in any defined environment variables. If
    found, import to main config."""
    import logging
    import os

    if 'GAD_REPO_URL' not in os.environ:
        return

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

    return repo_config


def get_config_file_path(env_config, argv_config, search_target):
    import os

    # Config file path provided in argument vector?
    if 'config' in argv_config and argv_config['config']:
        config_file_path = os.path.realpath(argv_config['config'])

    # Config file path provided in environment variable?
    elif 'config' in env_config and env_config['config']:
        config_file_path = os.path.realpath(env_config['config'])

    # Search file system
    else:

        # Directories to scan for config files
        target_directories = [
            os.getcwd(),  # cwd
            search_target  # script path
        ]

        config_file_path = find_config_file(target_directories)

    return config_file_path
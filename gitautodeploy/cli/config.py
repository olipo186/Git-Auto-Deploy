def get_config_defaults():
    """Get the default configuration values."""

    config = {}
    config['quiet'] = False
    config['daemon-mode'] = False
    config['config'] = None
    config['ssh-keyscan'] = False
    config['force'] = False
    config['ssl'] = False
    config['ssl-pem-file'] = '~/.gitautodeploy.pem'
    config['pidfilepath'] = '~/.gitautodeploy.pid'
    config['logfilepath'] = None
    config['host'] = '0.0.0.0'
    config['port'] = 8001
    config['intercept-stdout'] = True

    # Record all log levels by default
    config['log-level'] = 'NOTSET'

    # Include details with deploy command return codes in HTTP response. Causes
    # to await any git pull or deploy command actions before it sends the
    # response.
    config['detailed-response'] = False

    # Log incoming webhook requests in a way they can be used as test cases
    config['log-test-case'] = False
    config['log-test-case-dir'] = None

    config['web-ui'] = {
        'enabled': False,
        'remote-whitelist': ['127.0.0.1']
    }

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

    if 'GAD_FORCE' in os.environ:
        config['force'] = True

    if 'GAD_SSL' in os.environ:
        config['ssl'] = True

    if 'GADGAD_SSL_PEM_FILE_SSL' in os.environ:
        config['ssl-pem-file'] = os.environ['GAD_SSL_PEM_FILE']

    if 'GAD_PID_FILE' in os.environ:
        config['pidfilepath'] = os.environ['GAD_PID_FILE']

    if 'GAD_LOG_FILE' in os.environ:
        config['logfilepath'] = os.environ['GAD_LOG_FILE']

    if 'GAD_HOST' in os.environ:
        config['host'] = os.environ['GAD_HOST']

    if 'GAD_PORT' in os.environ:
        config['port'] = int(os.environ['GAD_PORT'])

    return config

def get_config_from_argv(argv):
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--daemon-mode",
                        help="run in background (daemon mode)",
                        dest="daemon-mode",
                        action="store_true")

    parser.add_argument("-q", "--quiet",
                        help="supress console output",
                        dest="quiet",
                        action="store_true")

    parser.add_argument("-c", "--config",
                        help="custom configuration file",
                        dest="config",
                        type=str)

    parser.add_argument("--ssh-keyscan",
                        help="scan repository hosts for ssh keys",
                        dest="ssh-keyscan",
                        action="store_true")

    parser.add_argument("--force",
                        help="kill any process using the configured port",
                        dest="force",
                        action="store_true")

    parser.add_argument("--pid-file",
                        help="specify a custom pid file",
                        dest="pidfilepath",
                        type=str)

    parser.add_argument("--log-file",
                        help="specify a log file",
                        dest="logfilepath",
                        type=str)

    parser.add_argument("--log-level",
                        help="specify log level",
                        dest="log-level",
                        type=str)

    parser.add_argument("--host",
                        help="address to bind to",
                        dest="host",
                        type=str)

    parser.add_argument("--port",
                        help="port to bind to",
                        dest="port",
                        type=int)

    parser.add_argument("--ssl",
                        help="use ssl",
                        dest="ssl",
                        action="store_true")

    parser.add_argument("--ssl-pem",
                        help="path to ssl pem file",
                        dest="ssl-pem",
                        type=str)

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
    if 'pidfilepath' in config and config['pidfilepath']:
        config['pidfilepath'] = os.path.expanduser(config['pidfilepath'])

    if 'logfilepath' in config and config['logfilepath']:
        config['logfilepath'] = os.path.expanduser(config['logfilepath'])

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

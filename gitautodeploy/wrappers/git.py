class GitWrapper():
    """Wraps the git client. Currently uses git through shell command
    invocations."""

    def __init__(self):
        pass

    @staticmethod
    def init(repo_config):
        """Init remote url of the repo from the git server"""
        import logging
        from process import ProcessWrapper
        import os
        import platform

        logger = logging.getLogger()
        logger.info("Initializing repository %s" % repo_config['path'])

        commands = []

        # On Windows, bash command needs to be run using bash.exe. This assumes bash.exe
        # (typically installed under C:\Program Files\Git\bin) is in the system PATH.
        if platform.system().lower() == "windows":
            commands.append('bash -c "cd \\"' + repo_config['path'] + '\\" && unset GIT_DIR"')
        else:
            commands.append('unset GIT_DIR')

        commands.append('git remote set-url ' + repo_config['remote'] + " " + repo_config['url'])
        commands.append('git fetch ' + repo_config['remote'])
        commands.append('git checkout -f -B ' + repo_config['branch'] + ' -t ' + repo_config['remote'] + '/' + repo_config['branch'])
        commands.append('git submodule update --init --recursive')

        # All commands need to success
        for command in commands:
            res = ProcessWrapper().call(command, cwd=repo_config['path'], shell=True)

            if res != 0:
                logger.error("Command '%s' failed with exit code %s" % (command, res))
                break

        if res == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully initialized" % repo_config['path'])
        else:
            logger.error("Unable to init repository %s" % repo_config['path'])

        return int(res)

    @staticmethod
    def pull(repo_config):
        """Pulls the latest version of the repo from the git server"""
        import logging
        from process import ProcessWrapper
        import os
        import platform

        logger = logging.getLogger()
        logger.info("Updating repository %s" % repo_config['path'])

        # Only pull if there is actually a local copy of the repository
        if 'path' not in repo_config:
            logger.info('No local repository path configured, no pull will occure')
            return 0

        commands = []

        # On Windows, bash command needs to be run using bash.exe. This assumes bash.exe
        # (typically installed under C:\Program Files\Git\bin) is in the system PATH.
        if platform.system().lower() == "windows":
            commands.append('bash -c "cd \\"' + repo_config['path'] + '\\" && unset GIT_DIR"')
        else:
            commands.append('unset GIT_DIR')

        commands.append('git fetch ' + repo_config['remote'])
        commands.append('git reset --hard ' + repo_config['remote'] + "/" + repo_config['branch'])
        commands.append('git submodule update --init --recursive')

        # All commands need to success
        for command in commands:
            res = ProcessWrapper().call(command, cwd=repo_config['path'], shell=True)

            if res != 0:
                logger.error("Command '%s' failed with exit code %s" % (command, res))
                break

        if res == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully updated" % repo_config['path'])
        else:
            logger.error("Unable to update repository %s" % repo_config['path'])

        return int(res)

    @staticmethod
    def clone(repo_config):
        """Clones the latest version of the repo from the git server"""
        import logging
        from process import ProcessWrapper
        import os
        import platform

        logger = logging.getLogger()
        logger.info("Cloning repository %s" % repo_config['path'])

        # Only pull if there is actually a local copy of the repository
        if 'path' not in repo_config:
            logger.info('No local repository path configured, no clone will occure')
            return 0

        commands = []
        commands.append('unset GIT_DIR')
        commands.append('git clone --recursive ' + repo_config['url'] + ' -b ' + repo_config['branch'] + ' ' + repo_config['path'])

        # All commands need to success
        for command in commands:
            res = ProcessWrapper().call(command, shell=True)

            if res != 0:
                logger.error("Command '%s' failed with exit code %s" % (command, res))
                break

        if res == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully cloned" % repo_config['url'])
        else:
            logger.error("Unable to clone repository %s" % repo_config['url'])

        return int(res)

    @staticmethod
    def deploy(repo_config):
        """Executes any supplied post-pull deploy command"""
        from process import ProcessWrapper
        import logging
        logger = logging.getLogger()

        if 'path' in repo_config:
            path = repo_config['path']

        if not 'deploy_commands' in repo_config or len(repo_config['deploy_commands']) == 0:
            logger.info('No deploy commands configured')
            return []

        logger.info('Executing %s deploy commands' % str(len(repo_config['deploy_commands'])))

        # Use repository path as default cwd when executing deploy commands
        cwd = (repo_config['path'] if 'path' in repo_config else None)

        res = []
        for cmd in repo_config['deploy_commands']:
            res.append(ProcessWrapper().call([cmd], cwd=cwd, shell=True))

        logger.info('%s commands executed with status; %s' % (str(len(res)), str(res)))

        return res

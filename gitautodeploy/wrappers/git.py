class GitWrapper():
    """Wraps the git client. Currently uses git through shell command
    invocations."""

    def __init__(self):
        pass

    @staticmethod
    def pull(repo_config):
        """Pulls the latest version of the repo from the git server"""
        import logging
        from process import ProcessWrapper
        import os

        logger = logging.getLogger()
        logger.info("Updating repository %s" % repo_config['path'])

        # Only pull if there is actually a local copy of the repository
        if 'path' not in repo_config:
            logger.info('No local repository path configured, no pull will occure')
            return 0

        cmd =   'unset GIT_DIR ' + \
                '&& git fetch ' + repo_config['remote'] + \
                '&& git reset --hard ' + repo_config['remote'] + '/' + repo_config['branch'] + ' ' + \
                '&& git submodule init ' + \
                '&& git submodule update'

        # '&& git update-index --refresh ' +\
        res = ProcessWrapper().call([cmd], cwd=repo_config['path'], shell=True)

        if res == 0 and os.path.isdir(repo_config['path']):
            logger.info("Repository %s successfully updated" % repo_config['path'])
        else:
            logger.error("Unable to update repository %s" % repo_config['path'])

        return int(res)

    @staticmethod
    def clone(url, branch, path):
        from process import ProcessWrapper
        res = ProcessWrapper().call(['git clone --recursive ' + url + ' -b ' + branch + ' ' + path], shell=True)
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
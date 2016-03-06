
class WebhookRequestParser(object):
    """Abstract parent class for git service parsers. Contains helper
    methods."""

    def __init__(self, config):
        self._config = config

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
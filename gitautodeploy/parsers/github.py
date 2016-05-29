from common import WebhookRequestParser

class GitHubRequestParser(WebhookRequestParser):

    def get_repo_params_from_request(self, request_headers, request_body):
        import json
        import logging

        logger = logging.getLogger()
        data = json.loads(request_body)

        repo_urls = []
        ref = ""
        action = ""

        github_event = 'x-github-event' in request_headers and request_headers['x-github-event']

        logger.debug("Received '%s' event from GitHub" % github_event)

        if 'repository' not in data:
            logger.error("Unable to recognize data format")
            return [], ref or "master", action

        # One repository may posses multiple URLs for different protocols
        for k in ['url', 'git_url', 'clone_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        if 'pull_request' in data:
            if 'base' in data['pull_request']:
                if 'ref' in data['pull_request']['base']:
                    ref = data['pull_request']['base']['ref']
                    logger.debug("Pull request to branch '%s' was fired" % ref)
        elif 'ref' in data:
            ref = data['ref']
            logger.debug("Push to branch '%s' was fired" % ref)

        if 'action' in data:
            action = data['action']
            logger.debug("Action '%s' was fired" % action)

        # Get a list of configured repositories that matches the incoming web hook reqeust
        items = self.get_matching_repo_configs(repo_urls)

        repo_configs = []
        for repo_config in items:

            # Validate secret token if present
            if 'secret-token' in repo_config and 'x-hub-signature' in request_headers:
                if not self.verify_signature(repo_config['secret-token'], request_body, request_headers['x-hub-signature']):
                    logger.warning("Request signature does not match the 'secret-token' configured for repository %s." % repo_config['url'])
                    continue

            repo_configs.append(repo_config)

        return repo_configs, ref or "master", action, repo_urls

    def verify_signature(self, token, body, signature):
        import hashlib
        import hmac

        result = "sha1=" + hmac.new(str(token), body, hashlib.sha1).hexdigest()
        return result == signature

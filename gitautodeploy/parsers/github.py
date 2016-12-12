from common import WebhookRequestParser

class GitHubRequestParser(WebhookRequestParser):

    def get_repo_configs(self, request_headers, request_body, action):
        import json

        data = json.loads(request_body)

        repo_urls = []

        github_event = 'x-github-event' in request_headers and request_headers['x-github-event']

        action.log_info("Received '%s' event from GitHub" % github_event)

        if 'repository' not in data:
            action.log_error("Unable to recognize data format")
            return []

        # One repository may posses multiple URLs for different protocols
        for k in ['url', 'git_url', 'clone_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = self.get_matching_repo_configs(repo_urls, action)

        return repo_configs

    def validate_request(self, request_headers, repo_configs, action):

        for repo_config in repo_configs:

            # Validate secret token if present
            if 'secret-token' in repo_config and 'x-hub-signature' in request_headers:
                if not self.verify_signature(repo_config['secret-token'], request_body, request_headers['x-hub-signature']):
                    action.log_info("Request signature does not match the 'secret-token' configured for repository %s." % repo_config['url'])
                    return False

        return True

    def verify_signature(self, token, body, signature):
        import hashlib
        import hmac

        result = "sha1=" + hmac.new(str(token), body, hashlib.sha1).hexdigest()
        return result == signature

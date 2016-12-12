from common import WebhookRequestParser

class CodingRequestParser(WebhookRequestParser):

    def get_repo_configs(self, request_headers, request_body, action):
        import json

        data = json.loads(request_body)

        repo_urls = []

        coding_event = 'x-coding-event' in request_headers and request_headers['x-coding-event']

        if 'repository' not in data:
            action.log_error("Unable to recognize data format")
            return []

        # One repository may posses multiple URLs for different protocols
        for k in ['web_url', 'https_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        # Get a list of configured repositories that matches the incoming web hook reqeust
        items = self.get_matching_repo_configs(repo_urls, action)

        repo_configs = []
        for repo_config in items:
            # Validate secret token if present
            if 'secret-token' in repo_config:
                if 'token' not in data or not self.verify_token(repo_config['secret-token'], data['token']):
                    action.log_warning("Request token does not match the 'secret-token' configured for repository %s." % repo_config['url'])
                    continue

            repo_configs.append(repo_config)

        return repo_configs


    def verify_token(self, secret_token, request_token):
        return secret_token == request_token

from common import WebhookRequestParser

class GenericRequestParser(WebhookRequestParser):

    def get_repo_configs(self, request_headers, request_body, action):
        import json

        data = json.loads(request_body)

        repo_urls = []

        action.log_info("Received event from unknown origin. Assume generic data format.")

        if 'repository' not in data:
            action.log_error("Unable to recognize data format")
            return []

        # One repository may posses multiple URLs for different protocols
        for k in ['url', 'git_http_url', 'git_ssh_url', 'http_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = self.get_matching_repo_configs(repo_urls, action)

        return repo_configs


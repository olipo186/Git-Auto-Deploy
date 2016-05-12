from common import WebhookRequestParser

class GenericRequestParser(WebhookRequestParser):

    def get_repo_params_from_request(self, request_headers, request_body):
        import json
        import logging

        logger = logging.getLogger()
        data = json.loads(request_body)

        repo_urls = []
        ref = ""
        action = ""

        logger.debug("Received event from unknown origin. Assume generic data format.")

        if 'repository' not in data:
            logger.error("Unable to recognize data format")
            return [], ref or "master", action

        # One repository may posses multiple URLs for different protocols
        for k in ['url', 'git_http_url', 'git_ssh_url', 'http_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = self.get_matching_repo_configs(repo_urls)

        return repo_configs, ref or "master", action, repo_urls
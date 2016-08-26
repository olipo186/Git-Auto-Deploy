from common import WebhookRequestParser

class CodingRequestParser(WebhookRequestParser):

    def get_repo_params_from_request(self, request_headers, request_body):
        import json
        import logging

        logger = logging.getLogger()
        data = json.loads(request_body)

        repo_urls = []
        ref = ""
        action = ""

        coding_event = 'x-coding-event' in request_headers and request_headers['x-coding-event']

        logger.debug("Received '%s' event from Coding" % coding_event)

        if 'repository' not in data:
            logger.error("Unable to recognize data format")
            return [], ref or "master", action

        # One repository may posses multiple URLs for different protocols
        for k in ['web_url', 'https_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        # extract the branch
        if 'ref' in data:
            ref = data['ref']

        # set the action
        if 'event' in data:
            action = data['event']

        # Get a list of configured repositories that matches the incoming web hook reqeust
        items = self.get_matching_repo_configs(repo_urls)

        repo_configs = []
        for repo_config in items:
            # Validate secret token if present
            if 'secret-token' in repo_config:
                if 'token' not in data or not self.verify_token(repo_config['secret-token'], data['token']):
                    logger.warning("Request token does not match the 'secret-token' configured for repository %s." % repo_config['url'])
                    continue

            repo_configs.append(repo_config)

        return repo_configs, ref or "master", action, repo_urls


    def verify_token(self, secret_token, request_token):
        return secret_token == request_token

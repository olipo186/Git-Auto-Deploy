from common import WebhookRequestParser

class GitLabRequestParser(WebhookRequestParser):

    def get_repo_params_from_request(self, request_headers, request_body):
        import json
        import logging

        logger = logging.getLogger()
        data = json.loads(request_body)

        repo_urls = []
        ref = ""
        action = ""

        gitlab_event = 'x-gitlab-event' in request_headers and request_headers['x-gitlab-event']

        logger.debug("Received '%s' event from GitLab" % gitlab_event)

        if 'repository' not in data:
            logger.error("Unable to recognize data format")
            return [], ref or "master", action

        # One repository may posses multiple URLs for different protocols
        for k in ['url', 'git_http_url', 'git_ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        # extract the branch
        if 'ref' in data:
            ref = data['ref']

        # set the action
        if 'object_kind' in data:
            action = data['object_kind']

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = self.get_matching_repo_configs(repo_urls)

        return repo_configs, ref or "master", action, repo_urls


class GitLabCIRequestParser(WebhookRequestParser):

    def get_repo_params_from_request(self, request_headers, request_body):
        import json
        import logging

        logger = logging.getLogger()
        data = json.loads(request_body)

        repo_urls = []
        ref = ""
        action = ""

        logger.debug('Received event from Gitlab CI')

        if 'push_data' not in data:
            logger.error("Unable to recognize data format")
            return [], ref or "master", action

        # Only add repositories if the build is successful. Ignore it in other case.
        if data['build_status'] == "success":
            for k in ['url', 'git_http_url', 'git_ssh_url']:
                if k in data['push_data']['repository']:
                    repo_urls.append(data['push_data']['repository'][k])
        else:
            logger.warning("Gitlab CI build '%d' has status '%s'. Not pull will be done" % (
                data['build_id'], data['build_status']))

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = self.get_matching_repo_configs(repo_urls)

        return repo_configs, ref or "master", action, repo_urls
from common import WebhookRequestParser

class GitLabCIRequestParser(WebhookRequestParser):

    def get_repo_configs(self, request_headers, request_body, action):
        import json

        data = json.loads(request_body)

        repo_urls = []

        action.log_info('Received event from Gitlab CI')

        if 'repository' not in data:
            action.log_error("Unable to recognize data format")
            return []

        # Only add repositories if the build is successful. Ignore it in other case.
        if data['build_status'] == "success":
            for k in ['url', 'git_http_url', 'git_ssh_url']:
                for n in ['repository', 'project']:
                    if n in data and k in data[n]:
                        repo_urls.append(data[n][k])
        else:
            action.log_warning("Gitlab CI build '%d' has status '%s'. Not pull will be done" % (data['build_id'], data['build_status']))

        # Get a list of configured repositories that matches the incoming web hook reqeust
        repo_configs = self.get_matching_repo_configs(repo_urls, action)

        return repo_configs

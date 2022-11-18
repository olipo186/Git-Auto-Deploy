from .base import WebhookRequestParserBase


class BitBucketRequestParser(WebhookRequestParserBase):

    def get_matching_projects(self, request_headers, request_body, action):
        import json

        data = json.loads(request_body)

        repo_urls = []

        action.log_debug("Received event from BitBucket")

        if 'repository' not in data:
            action.log_error("Unable to recognize data format")
            return []

        # One repository may posses multiple URLs for different protocols
        for k in ['url', 'git_url', 'clone_url', 'ssh_url']:
            if k in data['repository']:
                repo_urls.append(data['repository'][k])

        if 'full_name' in data['repository']:
            repo_urls.append('git@bitbucket.org:%s.git' % data['repository']['full_name'])

            # Add a simplified version of the bitbucket HTTPS URL - without the username@bitbucket.com part. This is
            # needed since the configured repositories might be configured using a different username.
            repo_urls.append('https://bitbucket.org/%s.git' % (data['repository']['full_name']))

        if 'fullName' in data['repository']:
            # For Bitbucket Server add repository name (OWNER/REPO_NAME).
            # Support "Post Webhooks for Bitbucket".
            repo_urls.append(data['repository']['fullName'])

        if 'slug' in data['repository']:
            # For Bitbucket Server add repository slug.
            # Support "Post-Receive WebHooks" and "Post Webhooks for Bitbucket".
            repo_urls.append(data['repository']['slug'])

        if 'changes' in data:
            repo_urls.append(data['changes'][0])

        # Get a list of configured repositories that matches the incoming web hook request
        repo_configs = self.get_matching_repo_configs(repo_urls, action)

        return repo_configs

from .parsers import CodingRequestParser, GitLabCIRequestParser
from .parsers import GitLabRequestParser, GitHubRequestParser
from .parsers import BitBucketRequestParser, GenericRequestParser


class WebbhookRequestProcessor(object):

    def get_service_handler(self, request_headers, request_body, action):
        """Parses the incoming request and attempts to determine whether
        it originates from GitHub, GitLab or any other known service."""
        import json

        payload = json.loads(request_body)

        if not isinstance(payload, dict):
            raise ValueError("Invalid JSON object")

        user_agent = 'user-agent' in request_headers and request_headers['user-agent']
        content_type = 'content-type' in request_headers and request_headers['content-type']

        # Assume Coding if the X-Coding-Event HTTP header is set
        if 'x-coding-event' in request_headers:
            return CodingRequestParser

        # Assume GitLab if the X-Gitlab-Event HTTP header is set
        elif 'x-gitlab-event' in request_headers:

            # Special Case for Gitlab CI
            if content_type == "application/json" and "build_status" in payload:
                return GitLabCIRequestParser
            else:
                return GitLabRequestParser

        # Assume GitHub if the X-GitHub-Event HTTP header is set
        elif 'x-github-event' in request_headers:

            return GitHubRequestParser

        # Assume BitBucket if the User-Agent HTTP header is set to
        # 'Bitbucket-Webhooks/2.0' (or something similar)
        elif user_agent and user_agent.lower().find('bitbucket') != -1:

            return BitBucketRequestParser

        # This handles old GitLab requests and Gogs requests for example.
        elif content_type == "application/json":

            action.log_info("Received event from unknown origin.")
            return GenericRequestParser

        action.log_error("Unable to recognize request origin. Don't know how to handle the request.")
        return

    def execute_webhook(self, repo_configs, request_headers, request_body, action):
        """Verify that the suggested repositories has matching settings and
        issue git pull and/or deploy commands."""
        import os
        import time
        import logging
        from .wrappers import GitWrapper
        from .lock import Lock
        import json

        logger = logging.getLogger()
        payload = json.loads(request_body)

        result = []

        # Process each matching repository
        for repo_config in repo_configs:

            repo_result = {}

            # In case there is no path configured for the repository, no pull will
            # be made.
            if 'path' not in repo_config:
                res = GitWrapper.deploy(repo_config)
                repo_result['deploy'] = res
                result.append(repo_result)
                continue

            # If the path does not exist, a warning will be raised and no pull or
            # deploy will be made.
            if not os.path.isdir(repo_config['path']):
                action.log_error("The repository '%s' does not exist locally. Make sure it was pulled properly without errors by reviewing the log." % repo_config['path'])
                result.append(repo_result)
                continue

            # If the path is not writable, a warning will be raised and no pull or
            # deploy will be made.
            if not os.access(repo_config['path'], os.W_OK):
                action.log_error("The path '%s' is not writable. Make sure that GAD has write access to that path." % repo_config['path'])
                result.append(repo_result)
                continue

            running_lock = Lock(os.path.join(repo_config['path'], 'status_running'))
            waiting_lock = Lock(os.path.join(repo_config['path'], 'status_waiting'))
            try:

                # Attempt to obtain the status_running lock
                while not running_lock.obtain():

                    # If we're unable, try once to obtain the status_waiting lock
                    if not waiting_lock.has_lock() and not waiting_lock.obtain():
                        action.log_error("Unable to obtain the status_running lock nor the status_waiting lock. Another process is already waiting, so we'll ignore the request.")

                        # If we're unable to obtain the waiting lock, ignore the request
                        break

                    # Keep on attempting to obtain the status_running lock until we succeed
                    time.sleep(5)

                n = 4
                res = None
                while n > 0:

                    # Attempt to pull up a maximum of 4 times
                    res = GitWrapper.pull(repo_config)
                    repo_result['git pull'] = res

                    # Return code indicating success?
                    if res == 0:
                        break

                    n -= 1

                if 0 < n:
                    res = GitWrapper.deploy(repo_config)
                    repo_result['deploy'] = res

            #except Exception as e:
            #    logger.error('Error during \'pull\' or \'deploy\' operation on path: %s' % repo_config['path'])
            #    logger.error(e)
            #    raise e

            finally:

                # Release the lock if it's ours
                if running_lock.has_lock():
                    running_lock.release()

                # Release the lock if it's ours
                if waiting_lock.has_lock():
                    waiting_lock.release()

                result.append(repo_result)

        action.log_info("Deploy commands were executed")
        action.set_waiting(False)
        action.set_success(True)

        return result


class WebhookRequestFilter(object):

    def passes_payload_filter(self, payload_filters, payload, action):
        import logging

        logger = logging.getLogger()

        # At least one filter must match
        for filter in payload_filters:

            # All options specified in the filter must match
            for filter_key, filter_value in filter.items():

                # Ignore filters with value None (let them pass)
                if filter_value == None:
                    continue

                # Interpret dots in filter name as path notations 
                node_value = payload
                for node_key in filter_key.split('.'):

                    # If the path is not valid the filter does not match
                    if not node_key in node_value:
                        action.log_info("Filter '%s' does not match since the path is invalid" % (filter_key))

                        # Filter does not match, do not process this repo config
                        return False

                    node_value = node_value[node_key]

                if filter_value == node_value:
                    continue

                # If the filter value is set to True. the filter
                # will pass regardless of the actual value
                if filter_value == True:
                    continue

                action.log_debug("Filter '%s' does not match ('%s' != '%s')" % (filter_key, filter_value, (str(node_value)[:75] + '..') if len(str(node_value)) > 75 else str(node_value)))

                # Filter does not match, do not process this repo config
                return False

        # Filter does match, proceed
        return True

    def passes_header_filter(self, header_filter, request_headers):
        import logging

        logger = logging.getLogger()

        # At least one filter must match
        for key in header_filter:

            # Verify that the request has the required header attribute
            if key.lower() not in request_headers:
                return False

            # "True" indicates that any header value is accepted
            if header_filter[key] is True:
                continue

            # Verify that the request has the required header value
            if header_filter[key] != request_headers[key.lower()]:
                return False

        # Filter does match, proceed
        return True

    def apply_filters(self, repo_configs, request_headers, request_body, action):
        """Verify that the suggested repositories has matching settings and
        issue git pull and/or deploy commands."""
        import os
        import time
        import logging
        from .wrappers import GitWrapper
        from .lock import Lock
        import json

        logger = logging.getLogger()
        payload = json.loads(request_body)

        matches = []

        # Process each matching repository
        for repo_config in repo_configs:

            # Verify that all payload filters matches the request (if any payload filters are specified)
            if 'payload-filter' in repo_config and not self.passes_payload_filter(repo_config['payload-filter'], payload, action):

                # Filter does not match, do not process this repo config
                continue

            # Verify that all header filters matches the request (if any header filters are specified)
            if 'header-filter' in repo_config and not self.passes_header_filter(repo_config['header-filter'], request_headers):

                # Filter does not match, do not process this repo config
                continue

            matches.append(repo_config)

        return matches
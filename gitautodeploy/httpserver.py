from BaseHTTPServer import BaseHTTPRequestHandler


class FilterMatchError(Exception):
    """Used to describe when a filter does not match a request."""
    pass

def WebhookRequestHandlerFactory(config):
    class WebhookRequestHandler(BaseHTTPRequestHandler, object):
        """Extends the BaseHTTPRequestHandler class and handles the incoming
        HTTP requests."""

        def __init__(self, *args, **kwargs):
             #do_stuff_with(self, init_args)
             self._config = config
             super(WebhookRequestHandler, self).__init__(*args, **kwargs)

        def do_POST(self):
            """Invoked on incoming POST requests"""
            from threading import Timer
            import logging
            import json

            logger = logging.getLogger()
            logger.info('Incoming request from %s:%s' % (self.client_address[0], self.client_address[1]))

            content_type = self.headers.getheader('content-type')
            content_length = int(self.headers.getheader('content-length'))
            request_body = self.rfile.read(content_length)

            # Test case debug data
            test_case = {
                'headers': dict(self.headers),
                'payload': json.loads(request_body),
                'config': {},
                'expected': {'status': 200, 'data': [{'deploy': 0}]}
            }

            # Extract request headers and make all keys to lowercase (makes them easier to compare)
            request_headers = dict(self.headers)
            request_headers = dict((k.lower(), v) for k, v in request_headers.iteritems())

            try:

                # Will raise a ValueError exception if it fails
                ServiceRequestParser = self.figure_out_service_from_request(request_headers, request_body)

                # Unable to identify the source of the request
                if not ServiceRequestParser:
                    self.send_error(400, 'Unrecognized service')
                    logger.error('Unable to find appropriate handler for request. The source service is not supported.')
                    test_case['expected']['status'] = 400
                    return

                # Send HTTP response before the git pull and/or deploy commands?
                if not 'detailed-response' in self._config or not self._config['detailed-response']:
                    self.send_response(200, 'OK')
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()

                logger.info('Handling the request with %s' % ServiceRequestParser.__name__)

                # Could be GitHubParser, GitLabParser or other
                repo_configs, ref, action, webhook_urls = ServiceRequestParser(self._config).get_repo_params_from_request(request_headers, request_body)
                logger.debug("Event details - ref: %s; action: %s" % (ref or "master", action))

                if not ServiceRequestParser(self._config).validate_request(request_headers, repo_configs):
                    self.send_error(400, 'Bad request')
                    test_case['expected']['status'] = 400
                    return

                if len(repo_configs) == 0:
                    self.send_error(400, 'Bad request')
                    logger.warning('The URLs references in the webhook did not match any repository entry in the config. For this webhook to work, make sure you have at least one repository configured with one of the following URLs; %s' % ', '.join(webhook_urls))
                    test_case['expected']['status'] = 400
                    return

                # Make git pulls and trigger deploy commands
                res = self.process_repositories(repo_configs, ref, action, request_body, request_headers)

                if 'detailed-response' in self._config and self._config['detailed-response']:
                    self.send_response(200, 'OK')
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(res))
                    self.wfile.close()

                # Add additional test case data
                test_case['config'] = {
                    'url': 'url' in repo_configs[0] and repo_configs[0]['url'],
                    'branch': 'branch' in repo_configs[0] and repo_configs[0]['branch'],
                    'remote': 'remote' in repo_configs[0] and repo_configs[0]['remote'],
                    'deploy': 'echo test!'
                }

            except ValueError, e:
                self.send_error(400, 'Unprocessable request')
                logger.warning('Unable to process incoming request from %s:%s' % (self.client_address[0], self.client_address[1]))
                test_case['expected']['status'] = 400
                return

            except Exception, e:

                if 'detailed-response' in self._config and self._config['detailed-response']:
                    self.send_error(500, 'Unable to process request')

                test_case['expected']['status'] = 500

                raise e

            finally:

                # Save the request as a test case
                if 'log-test-case' in self._config and self._config['log-test-case']:
                    self.save_test_case(test_case)

        def log_message(self, format, *args):
            """Overloads the default message logging method to allow messages to
            go through our custom logger instead."""
            import logging
            logger = logging.getLogger()
            logger.info("%s - %s" % (self.client_address[0],
                                            format%args))

        def figure_out_service_from_request(self, request_headers, request_body):
            """Parses the incoming request and attempts to determine whether
            it originates from GitHub, GitLab or any other known service."""
            import json
            import logging
            import parsers

            logger = logging.getLogger()
            data = json.loads(request_body)

            if not isinstance(data, dict):
                raise ValueError("Invalid JSON object")

            user_agent = 'user-agent' in request_headers and request_headers['user-agent']
            content_type = 'content-type' in request_headers and request_headers['content-type']

            # Assume Coding if the X-Coding-Event HTTP header is set
            if 'x-coding-event' in request_headers:
                return parsers.CodingRequestParser

            # Assume GitLab if the X-Gitlab-Event HTTP header is set
            elif 'x-gitlab-event' in request_headers:

                # Special Case for Gitlab CI
                if content_type == "application/json" and "build_status" in data:
                    return parsers.GitLabCIRequestParser
                else:
                    return parsers.GitLabRequestParser

            # Assume GitHub if the X-GitHub-Event HTTP header is set
            elif 'x-github-event' in request_headers:

                return parsers.GitHubRequestParser

            # Assume BitBucket if the User-Agent HTTP header is set to
            # 'Bitbucket-Webhooks/2.0' (or something similar)
            elif user_agent and user_agent.lower().find('bitbucket') != -1:

                return parsers.BitBucketRequestParser

            # This handles old GitLab requests and Gogs requests for example.
            elif content_type == "application/json":

                logger.info("Received event from unknown origin.")
                return parsers.GenericRequestParser

            logger.error("Unable to recognize request origin. Don't know how to handle the request.")
            return

        def passes_payload_filter(self, payload_filters, data, action):
            import logging

            logger = logging.getLogger()

            # At least one filter must match
            for filter in payload_filters:

                # All options specified in the filter must match
                for filter_key, filter_value in filter.iteritems():

                    # Ignore filters with value None (let them pass)
                    if filter_value == None:
                        continue

                    # Support for earlier version so it's non-breaking functionality
                    if filter_key == 'action' and filter_value == action:
                        continue

                    # Interpret dots in filter name as path notations 
                    node_value = data
                    for node_key in filter_key.split('.'):

                        # If the path is not valid the filter does not match
                        if not node_key in node_value:
                            logger.info("Filter '%s' does not match since the path is invalid" % (filter_key))

                            # Filter does not match, do not process this repo config
                            return False

                        node_value = node_value[node_key]

                    if filter_value == node_value:
                        continue

                    # If the filter value is set to True. the filter
                    # will pass regardless of the actual value 
                    if filter_value == True:
                        continue

                    logger.info("Filter '%s'' does not match ('%s' != '%s')" % (filter_key, filter_value, (str(node_value)[:75] + '..') if len(str(node_value)) > 75 else str(node_value)))

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

        def process_repositories(self, repo_configs, ref, action, request_body, request_headers):
            """Verify that the suggested repositories has matching settings and
            issue git pull and/or deploy commands."""
            import os
            import time
            import logging
            from wrappers import GitWrapper
            from lock import Lock
            import json

            logger = logging.getLogger()
            data = json.loads(request_body)

            result = []

            # Process each matching repository
            for repo_config in repo_configs:

                repo_result = {}

                # Verify that all payload filters matches the request (if any payload filters are specified)
                if 'payload-filter' in repo_config and not self.passes_payload_filter(repo_config['payload-filter'], data, action):

                    # Filter does not match, do not process this repo config
                    continue

                # Verify that all header filters matches the request (if any header filters are specified)
                if 'header-filter' in repo_config and not self.passes_header_filter(repo_config['header-filter'], request_headers):

                    # Filter does not match, do not process this repo config
                    continue

                # In case there is no path configured for the repository, no pull will
                # be made.
                if not 'path' in repo_config:
                    res = GitWrapper.deploy(repo_config)
                    repo_result['deploy'] = res
                    result.append(repo_result)
                    continue

                # If the path does not exist, a warning will be raised and no pull or
                # deploy will be made.
                if not os.path.isdir(repo_config['path']):
                    logger.error("The repository '%s' does not exist locally. Make sure it was pulled " % repo_config['path'] +
                            "properly without errors by reviewing the log.")
                    result.append(repo_result)
                    continue

                # If the path is not writable, a warning will be raised and no pull or
                # deploy will be made.
                if not os.access(repo_config['path'], os.W_OK):
                    logger.error("The path '%s' is not writable. Make sure that GAD has write access to that path." % repo_config['path'])
                    result.append(repo_result)
                    continue

                running_lock = Lock(os.path.join(repo_config['path'], 'status_running'))
                waiting_lock = Lock(os.path.join(repo_config['path'], 'status_waiting'))
                try:

                    # Attempt to obtain the status_running lock
                    while not running_lock.obtain():

                        # If we're unable, try once to obtain the status_waiting lock
                        if not waiting_lock.has_lock() and not waiting_lock.obtain():
                            logger.error("Unable to obtain the status_running lock nor the status_waiting lock. Another process is " +
                                            "already waiting, so we'll ignore the request.")

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

            return result

        def save_test_case(self, test_case):
            """Log request information in a way it can be used as a test case."""
            import time
            import json
            import os

            # Mask some header values
            masked_headers = ['x-github-delivery', 'x-hub-signature']
            for key in test_case['headers']:
                if key in masked_headers:
                    test_case['headers'][key] = 'xxx'

            target = '%s-%s.tc.json' % (self.client_address[0], time.strftime("%Y%m%d%H%M%S"))
            if 'log-test-case-dir' in self._config and self._config['log-test-case-dir']:
                target = os.path.join(self._config['log-test-case-dir'], target)

            file = open(target, 'w')
            file.write(json.dumps(test_case, sort_keys=True, indent=4))
            file.close()

    return WebhookRequestHandler

class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Extends the BaseHTTPRequestHandler class and handles the incoming
    HTTP requests."""



from BaseHTTPServer import BaseHTTPRequestHandler


class FilterMatchError(Exception):
    """Used to describe when a filter does not match a request."""
    pass


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Extends the BaseHTTPRequestHandler class and handles the incoming
    HTTP requests."""

    def do_POST(self):
        """Invoked on incoming POST requests"""
        from threading import Timer
        import logging

        logger = logging.getLogger()

        content_type = self.headers.getheader('content-type')
        content_length = int(self.headers.getheader('content-length'))
        request_body = self.rfile.read(content_length)
        
        # Extract request headers and make all keys to lowercase (makes them easier to compare)
        request_headers = dict(self.headers)
        request_headers = dict((k.lower(), v) for k, v in request_headers.iteritems())

        ServiceRequestParser = self.figure_out_service_from_request(request_headers, request_body)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        # Unable to identify the source of the request
        if not ServiceRequestParser:
            logger.error('Unable to find appropriate handler for request. The source service is not supported.')
            return

        # Could be GitHubParser, GitLabParser or other
        repo_configs, ref, action, repo_urls = ServiceRequestParser(self._config).get_repo_params_from_request(request_headers, request_body)

        logger.info("Event details - ref: %s; action: %s" % (ref or "master", action))

        #if success:
        #    print "Successfullt handled request using %s" % ServiceHandler.__name__
        #else:
        #    print "Unable to handle request using %s" % ServiceHandler.__name__

        if len(repo_configs) == 0:
            logger.warning('Unable to find any of the repository URLs in the config: %s' % ', '.join(repo_urls))
            return

        # Wait one second before we do git pull (why?)
        Timer(1.0, self.process_repositories, (repo_configs,
                                               ref,
                                               action, request_body)).start()

    def log_message(self, format, *args):
        """Overloads the default message logging method to allow messages to
        go through our custom logger instead."""
        import logging
        logger = logging.getLogger()
        logger.info("%s - - [%s] %s\n" % (self.client_address[0],
                                          self.log_date_time_string(),
                                          format%args))

    def figure_out_service_from_request(self, request_headers, request_body):
        """Parses the incoming request and attempts to determine whether
        it originates from GitHub, GitLab or any other known service."""
        import json
        import logging
        import parsers

        logger = logging.getLogger()
        data = json.loads(request_body)

        user_agent = 'user-agent' in request_headers and request_headers['user-agent']
        content_type = 'content-type' in request_headers and request_headers['content-type']

        # Assume GitLab if the X-Gitlab-Event HTTP header is set
        if 'x-gitlab-event' in request_headers:

            logger.info("Received event from GitLab")
            return parsers.GitLabRequestParser

        # Assume GitHub if the X-GitHub-Event HTTP header is set
        elif 'x-github-event' in request_headers:

            logger.info("Received event from GitHub")
            return parsers.GitHubRequestParser

        # Assume BitBucket if the User-Agent HTTP header is set to
        # 'Bitbucket-Webhooks/2.0' (or something similar)
        elif user_agent and user_agent.lower().find('bitbucket') != -1:

            logger.info("Received event from BitBucket")
            return parsers.BitBucketRequestParser

        # Special Case for Gitlab CI
        elif content_type == "application/json" and "build_status" in data:

            logger.info('Received event from Gitlab CI')
            return parsers.GitLabCIRequestParser

        # This handles old GitLab requests and Gogs requests for example.
        elif content_type == "application/json":

            logger.info("Received event from unknown origin.")
            return parsers.GenericRequestParser

        logger.error("Unable to recognize request origin. Don't know how to handle the request.")
        return


    def process_repositories(self, repo_configs, ref, action, request_body):
        import os
        import time
        import logging
        from wrappers import GitWrapper
        from lock import Lock
        import json
        
        logger = logging.getLogger()
        data = json.loads(request_body)

        # Process each matching repository
        for repo_config in repo_configs:

            try:
                # Verify that all filters matches the request (if any filters are specified)
                if 'filters' in repo_config:

                    # at least one filter must match
                    for filter in repo_config['filters']:

                        # all options specified in the filter must match
                        for filter_key, filter_value in filter.iteritems():

                            # support for earlier version so it's non-breaking functionality
                            if filter_key == 'action' and filter_value == action:
                                continue

                            if filter_key not in data or filter_value != data[filter_key]:
                                raise FilterMatchError()

            except FilterMatchError as e:

                # Filter does not match, do not process this repo config
                continue
            
            # In case there is no path configured for the repository, no pull will
            # be made.
            if not 'path' in repo_config:
                GitWrapper.deploy(repo_config)
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
                while 0 < n and 0 != GitWrapper.pull(repo_config):
                    n -= 1

                if 0 < n:
                    GitWrapper.deploy(repo_config)

            except Exception as e:
                logger.error('Error during \'pull\' or \'deploy\' operation on path: %s' % repo_config['path'])
                logger.error(e)

            finally:

                # Release the lock if it's ours
                if running_lock.has_lock():
                    running_lock.release()

                # Release the lock if it's ours
                if waiting_lock.has_lock():
                    waiting_lock.release()

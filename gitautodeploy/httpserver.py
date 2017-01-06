def WebhookRequestHandlerFactory(config, event_store, server_status, is_https=False):
    """Factory method for webhook request handler class"""
    try:
        from SimpleHTTPServer import SimpleHTTPRequestHandler
    except ImportError as e:
        from http.server import SimpleHTTPRequestHandler

    class WebhookRequestHandler(SimpleHTTPRequestHandler, object):
        """Extends the BaseHTTPRequestHandler class and handles the incoming
        HTTP requests."""

        def __init__(self, *args, **kwargs):
             self._config = config
             self._event_store = event_store
             self._server_status = server_status
             self._is_https = is_https
             super(WebhookRequestHandler, self).__init__(*args, **kwargs)

        def end_headers (self):
            self.send_header('Access-Control-Allow-Origin', '*')
            SimpleHTTPRequestHandler.end_headers(self)

        def do_HEAD(self):
            import json

            if not self._config['web-ui-enabled']:
                self.send_error(403, "Web UI is not enabled")
                return

            if not self._is_https and self._config['web-ui-require-https']:

                # Attempt to redirect the request to HTTPS
                server_status = self.get_server_status()
                if 'https-uri' in server_status:
                    self.send_response(307)
                    self.send_header('Location', '%s%s' % (server_status['https-uri'], self.path))
                    self.end_headers()
                    return

                self.send_error(403, "Web UI is only accessible through HTTPS")
                return

            if not self.client_address[0] in self._config['web-ui-whitelist']:
                self.send_error(403, "%s is not allowed access" % self.client_address[0])
                return

            return SimpleHTTPRequestHandler.do_HEAD(self)

        def do_GET(self):
            import json

            if not self._config['web-ui-enabled']:
                self.send_error(403, "Web UI is not enabled")
                return

            if not self._is_https and self._config['web-ui-require-https']:

                # Attempt to redirect the request to HTTPS
                server_status = self.get_server_status()
                if 'https-uri' in server_status:
                    self.send_response(307)
                    self.send_header('Location', '%s%s' % (server_status['https-uri'], self.path))
                    self.end_headers()
                    return

                self.send_error(403, "Web UI is only accessible through HTTPS")
                return

            if not self.client_address[0] in self._config['web-ui-whitelist']:
                self.send_error(403, "%s is not allowed access" % self.client_address[0])
                return

            if self.path == "/api/status":
                data = {
                    'events': self._event_store.dict_repr(),
                }

                data.update(self.get_server_status())

                self.send_response(200, 'OK')
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
                return

            return SimpleHTTPRequestHandler.do_GET(self)

        def do_POST(self):
            """Invoked on incoming POST requests"""
            from threading import Timer
            import logging
            import json
            from .events import WebhookAction
            from .webhook import WebhookRequestFilter, WebbhookRequestProcessor
            import threading

            logger = logging.getLogger()

            content_length = int(self.headers.get('content-length'))
            request_body = self.rfile.read(content_length).decode('utf-8')

            # Extract request headers and make all keys to lowercase (makes them easier to compare)
            request_headers = dict(self.headers)
            request_headers = dict((k.lower(), v) for k, v in request_headers.items())

            action = WebhookAction(self.client_address, request_headers, request_body)
            event_store.register_action(action)
            action.set_waiting(True)

            action.log_info('Incoming request from %s:%s' % (self.client_address[0], self.client_address[1]))

            # Test case debug data
            test_case = {
                'headers': dict(self.headers),
                'payload': json.loads(request_body),
                'config': {},
                'expected': {'status': 200, 'data': [{'deploy': 0}]}
            }

            try:

                request_processor = WebbhookRequestProcessor()

                # Will raise a ValueError exception if it fails
                ServiceRequestHandler = request_processor.get_service_handler(request_headers, request_body, action)

                # Unable to identify the source of the request
                if not ServiceRequestHandler:
                    self.send_error(400, 'Unrecognized service')
                    test_case['expected']['status'] = 400
                    action.log_error("Unable to find appropriate handler for request. The source service is not supported")
                    return

                service_handler = ServiceRequestHandler(self._config)

                action.log_info("Handling the request with %s" % ServiceRequestHandler.__name__)

                # Could be GitHubParser, GitLabParser or other
                repo_configs = service_handler.get_repo_configs(request_headers, request_body, action)

                request_filter = WebhookRequestFilter()

                if len(repo_configs) == 0:
                    self.send_error(400, 'Bad request')
                    test_case['expected']['status'] = 400
                    action.log_error("No matching repository config")
                    return

                # Apply filters
                repo_configs = request_filter.apply_filters(repo_configs, request_headers, request_body, action)

                if not service_handler.validate_request(request_headers, repo_configs, action):
                    self.send_error(400, 'Bad request')
                    test_case['expected']['status'] = 400
                    action.log_warning("Request not valid")
                    return

                test_case['expected']['status'] = 200

                self.send_response(200, 'OK')
                self.send_header('Content-type', 'text/plain')
                self.end_headers()

                if len(repo_configs) == 0:
                    action.log_info("Filter does not match")
                    return

                action.log_info("Executing deploy commands")

                # Schedule the execution of the webhook (git pull and trigger deploy etc)
                thread = threading.Thread(target=request_processor.execute_webhook, args=[repo_configs, request_headers, request_body, action])
                thread.start()

                # Add additional test case data
                test_case['config'] = {
                    'url': 'url' in repo_configs[0] and repo_configs[0]['url'],
                    'branch': 'branch' in repo_configs[0] and repo_configs[0]['branch'],
                    'remote': 'remote' in repo_configs[0] and repo_configs[0]['remote'],
                    'deploy': 'echo test!'
                }

            except ValueError as e:
                self.send_error(400, 'Unprocessable request')
                action.log_warning('Unable to process incoming request from %s:%s' % (self.client_address[0], self.client_address[1]))
                test_case['expected']['status'] = 400
                action.set_waiting(False)
                action.set_success(False)
                return

            except Exception as e:

                if 'detailed-response' in self._config and self._config['detailed-response']:
                    self.send_error(500, 'Unable to process request')

                test_case['expected']['status'] = 500
                action.log_warning("Unable to process request")
                action.set_waiting(False)
                action.set_success(False)

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

        def get_server_status(self):
            """Generate a copy of the server status object that contains the public IP or hostname."""
            server_status = {}
            for item in self._server_status.items():
                key, value = item
                public_host = self.headers.get('host').split(':')[0]
                if key == 'http-uri':
                    server_status[key] = value.replace(self._config['http-host'], public_host)
                if key == 'https-uri':
                    server_status[key] = value.replace(self._config['https-host'], public_host)
                if key == 'wss-uri':
                    server_status[key] = value.replace(self._config['wss-host'], public_host)
            return server_status

    return WebhookRequestHandler


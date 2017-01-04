try:
    from autobahn.websocket import WebSocketServerProtocol
except ImportError:
    WebSocketServerProtocol = object

def WebSocketClientHandlerFactory(config, clients, event_store):
    """Factory method for webhook request handler class"""

    class WebSocketClientHandler(WebSocketServerProtocol, object):
        from .events import SystemEvent

        def __init__(self, *args, **kwargs):
            self._config = config
            self.clients = clients
            self.event_store = event_store
            import logging
            self.logger = logging.getLogger()
            super(WebSocketClientHandler, self).__init__(*args, **kwargs)

        def onConnect(self, request):
            self.logger.info("Client connecting: {0}".format(request.peer))

            # Validate the request
            if not self._config['web-ui']['enabled'] or not self.peer.host in self._config['web-ui']['remote-whitelist']:
                self.sendClose()
                logger.info("Unautorized connection attempt from %s" % self.peer.host)
                return

            self.clients.append(self)

        def onOpen(self):
            self.logger.info("WebSocket connection open.")

        def onMessage(self, payload, isBinary):
            self.logger.info("WebSocket connection open.")
            if isBinary:
                self.logger.info("Binary message received: {0} bytes".format(len(payload)))
            else:
                self.logger.info("Text message received: {0}".format(payload.decode('utf8')))

            for client in self.clients:
                client.sendMessage(payload, isBinary)

            # echo back message verbatim
            self.sendMessage(payload, isBinary)

        def onClose(self, wasClean, code, reason):
            self.logger.info("WebSocket connection closed: {0}".format(reason))

            if self in self.clients:
                self.clients.remove(self)

        def notify_refresh(self, payload):
            import json
            self.sendMessage(json.dumps({
                "event": "refresh",
                "payload": payload
            }))

    return WebSocketClientHandler

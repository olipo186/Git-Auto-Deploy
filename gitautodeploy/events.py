class SystemEvent(object):

    def __init__(self, name=None):
        import logging

        self.logger = logging.getLogger()
        self.hub = None
        self.messages = []
        self.name = name
        self.id = None
        self.waiting = None
        self.success = None

    def __repr__(self):
        if self.id:
            return "<SystemEvent:%s>" % self.id
        else:
            return "<SystemEvent>"

    def dict_repr(self):
        from time import time
        return {
            "id": self.id,
            "type": type(self).__name__,
            "timestamp": time(),
            "messages": self.messages,
            "waiting": self.waiting,
            "success": self.success
        }

    def register_hub(self, hub):
        self.hub = hub

    def register_message(self, message, level="INFO"):
        self.messages.append(message)
        self.hub.update_action(self, message)

    def notify(self):
        self.hub.notify(self)

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_waiting(self, value):
        self.waiting = value

    def set_success(self, value):
        self.success = value

    def log_debug(self, message):
        self.logger.debug(message)
        self.register_message(message, "DEBUG")

    def log_info(self, message):
        self.logger.info(message)
        self.register_message(message, "INFO")

    def log_warning(self, message):
        self.logger.warning(message)
        self.register_message(message, "WARNING")

    def log_error(self, message):
        self.logger.error(message)
        self.register_message(message, "ERROR")

    def log_critical(self, message):
        self.logger.critical(message)
        self.register_message(message, "CRITICAL")

    def update(self):
        self.hub.update_action(self)


class WebhookAction(SystemEvent):
    """Represents a webhook request event and keeps a copy of all incoming and outgoing data for monitoring purposes."""

    def __init__(self, client_address, request_headers, request_body):
        self.client_address = client_address
        self.request_headers = request_headers
        self.request_body = request_body
        super(WebhookAction, self).__init__()

    def __repr__(self):
        return "<WebhookAction>"

    def dict_repr(self):
        data = super(WebhookAction, self).dict_repr()
        data['client-address'] = self.client_address[0]
        data['client-port'] = self.client_address[1]
        data['request-headers'] = self.request_headers
        data['request-body'] = self.request_body
        return data


class StartupEvent(SystemEvent):

    def __init__(self, http_address=None, http_port=None, ws_address=None, ws_port=None):
        self.http_address = http_address
        self.http_port = http_port
        self.http_started = False
        self.ws_address = ws_address
        self.ws_port = ws_port
        self.ws_started = False
        super(StartupEvent, self).__init__()

    def __repr__(self):
        return "<StartupEvent>"

    def dict_repr(self):
        data = super(StartupEvent, self).dict_repr()
        data['http-address'] = self.http_address
        data['http-port'] = self.http_port
        data['http-started'] = self.http_started
        data['ws-address'] = self.ws_address
        data['ws-port'] = self.ws_port
        data['ws-started'] = self.ws_started
        return data


class EventStore(object):

    def __init__(self):
        self.actions = []
        self.observers = []
        self.next_id = 0

    def register_observer(self, observer):
        self.observers.append(observer)

    def unregister_observer(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def update_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update(*args, **kwargs)

    def register_action(self, event):
        event.set_id(self.next_id)
        event.register_hub(self)
        self.next_id = self.next_id + 1
        self.actions.append(event)
        self.update_observers(event=event)

        # Store max 100 actions
        if len(self.actions) > 100:
            self.actions.pop(0)

    def notify(self, event):
        self.update_observers(event=event)

    def update_action(self, event, message=None):
        self.update_observers(event=event, message=message)

    def dict_repr(self):
        action_repr = []
        for action in self.actions:
            action_repr.append(action.dict_repr())
        return action_repr

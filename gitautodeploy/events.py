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

    def __init__(self, address=None, port=None):
        self.address = address
        self.port = port
        super(StartupEvent, self).__init__()

    def __repr__(self):
        return "<StartupEvent>"

    def dict_repr(self):
        data = super(StartupEvent, self).dict_repr()
        data['address'] = self.address
        data['port'] = self.port
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

    def register_action(self, action):
        action.set_id(self.next_id)
        action.register_hub(self)
        self.next_id = self.next_id + 1
        self.actions.append(action)
        self.update_observers(action)

        # Store max 100 actions
        if len(self.actions) > 100:
            self.actions.pop(0)

    def notify(self, event):
        self.update_observers(event=event)

    def update_action(self, action, message=None):
        self.update_observers(action, message)

    def dict_repr(self):
        return map(lambda x: x.dict_repr(), self.actions)

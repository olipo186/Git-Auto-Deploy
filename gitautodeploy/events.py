class Action(object):

    def __init__(self, name=None):
        import logging

        self.logger = logging.getLogger()
        self.hub = None
        self.messages = []
        self.name = name

    def __repr__(self):
        if self.name:
            return "<Action:%s>" % self.name
        else:
            return "<Action>"

    def dict_repr(self):
        return {
            "messages": self.messages
        }

    def register_hub(self, hub):
        self.hub = hub

    def register_message(self, message, level="INFO"):
        self.messages.append(message)
        self.hub.update_action(self, message)

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


class WebhookAction(Action):
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
        data['request_headers'] = self.request_headers
        data['request_body'] = self.request_body
        return data


class EventStore(object):

    def __init__(self):
        self.actions = []
        self.observers = []

    def register_observer(self, observer):
        self.observers.append(observer)

    def unregister_observer(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def update_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update(*args, **kwargs)

    def register_action(self, action):
        action.register_hub(self)
        self.actions.append(action)
        self.update_observers(action)

        # Store max 100 actions
        if len(self.actions) > 100:
            self.actions.pop(0)

    def update_action(self, action, message=None):
        self.update_observers(action, message)

    def dict_repr(self):
        return map(lambda x: x.dict_repr(), self.actions)

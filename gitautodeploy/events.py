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
        self.hub.notify_observers(type="event-updated", event=self.dict_repr())

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_waiting(self, value):
        self.waiting = value
        self.hub.notify_observers(type="event-updated", event=self.dict_repr())

    def set_success(self, value):
        self.success = value
        self.hub.notify_observers(type="event-updated", event=self.dict_repr())
        self.hub.notify_observers(type="event-success", id=self.id, success=value)

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

    #def update(self):
    #    self.hub.notify_observers(type="event-updated", event=self.dict_repr())


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
        self.http_started = None
        self.ws_address = ws_address
        self.ws_port = ws_port
        self.ws_started = None
        self.waiting = True
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

    def set_http_started(self, value):
        self.http_started = value
        self.hub.notify_observers(type="event-updated", event=self.dict_repr())
        self.validate_success()

    def set_ws_started(self, value):
        self.ws_started = value
        self.hub.notify_observers(type="event-updated", event=self.dict_repr())
        self.validate_success()

    def validate_success(self):
        if self.http_started is not False and self.ws_started is not False:
            self.set_waiting(False)
            self.set_success(True)


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

    def notify_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update(*args, **kwargs)

    def register_action(self, event):
        event.set_id(self.next_id)
        event.register_hub(self)
        self.next_id = self.next_id + 1
        self.actions.append(event)
        self.notify_observers(type="new-event", event=event.dict_repr())

        # Store max 100 actions
        if len(self.actions) > 100:
            self.actions.pop(0)

    def dict_repr(self):
        action_repr = []
        for action in self.actions:
            action_repr.append(action.dict_repr())
        return action_repr

class Scanner:
    event_handlers = {}
    handled_bodies = set()

    def add_event(self, event):
        event_key = event["event"]
        if event_key in self.event_handlers:
            self.event_handlers[event_key](event)

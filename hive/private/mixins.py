from .trigger import trigger
from .connect import connect


class ConnectableMixin:

    def connect(self, *targets):
        for target in targets:
            connect(self, target)


class TriggerableMixin:

    def connect(self, *targets):
        for target in targets:
            trigger(self, target)

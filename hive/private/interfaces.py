from .trigger import trigger
from .connect import connect


class ConnectableMixin:

    def connect(self, other):
        return connect(self, other)


class TriggerableMixin:

    def connect(self, other):
        return trigger(self, other)
from ..functional.connect import connect
from ..functional.trigger import trigger


class ConnectableMixin:

    def connect(self, other):
        return connect(self, other)


class TriggerableMixin:

    def connect(self, other):
        return trigger(self, other)
from weakref import ref


class Pusher(object):

    def __init__(self, parent):
        self._targets = []
        self._parent = ref(parent)

    def add_target(self, target):
        assert callable(target)
        self._targets.append(target)

    def push(self, *args, **kwargs):
        for target in self._targets:
            # TODO: exception handling
            target(*args, **kwargs)

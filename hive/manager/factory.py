from ..contexts import get_mode, hive_modes


class ModeFactory(object):
    """Return appropriate class instance depending upon execution mode"""

    def __init__(self, name, **kwargs):
        self.name = name

        self.context_dict = ctx = {}

        for mode, cls in kwargs.items():
            assert mode in hive_modes, "Invalid argument for class context factory: {}".format(mode)
            ctx[mode] = cls

    def __call__(self, *args, **kwargs):
        mode = get_mode()

        try:
            cls = self.context_dict[mode]

        except KeyError:
            raise TypeError("{} cannot be used in {} mode".format(self.name, mode))

        return cls(*args, **kwargs)
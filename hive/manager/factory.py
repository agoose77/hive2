from ..contexts import get_mode, hive_modes

from logging import getLogger

logger = getLogger(__name__)


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

        try:
            return cls(*args, **kwargs)
        except:
            logger.exception("Unable to instantiate {} in {} mode".format(self.name, mode))
            raise

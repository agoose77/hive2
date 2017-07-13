from ..contexts import get_mode, HiveMode

from logging import getLogger

logger = getLogger(__name__)


class HiveModeFactory(object):
    """Return appropriate class instance depending upon execution mode"""

    def __init__(self, name, **kwargs):
        self._name = name
        self._context_dict = ctx = {}

        for mode_name, cls in kwargs.items():
            try:
                mode = HiveMode.__members__[mode_name]
            except KeyError:
                raise ValueError("Invalid argument for class context factory: {}".format(mode_name))
            ctx[mode] = cls

    @property
    def name(self):
        return self._name

    def __call__(self, *args, **kwargs):
        mode = get_mode()

        try:
            cls = self._context_dict[mode]

        except KeyError:
            raise TypeError("{} cannot be used in {} mode".format(self._name, mode.name))

        try:
            return cls(*args, **kwargs)
        except:
            logger.exception("Unable to instantiate {} in {} mode".format(self._name, mode.name))
            raise

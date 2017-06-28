from ..contexts import get_building_hive
from ..mixins import Bee


class HiveBee(Bee):
    # TODO: resolve method for arguments that are bees (returns a new HiveBee class?)

    def __init__(self):
        self._hive_object_cls = get_building_hive()
        assert get_building_hive() is not None

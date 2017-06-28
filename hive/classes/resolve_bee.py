from ..manager import memoize
from ..contexts import get_building_hive
from ..mixins import Bee, Bindable, Exportable, Nameable


class BindableResolveBee(Bee, Bindable, Nameable):

    def __init__(self, unbound_run_hive, bee):
        self._bee = bee
        self._unbound_run_hive = unbound_run_hive

        # For inspection purposes
        self._hive_object_cls = get_building_hive()

        # Support ResolveBees used for hive_objects
        if hasattr(bee, "_hive_object"):
            self._hive_object = bee._hive_object

        else:
            self._hive_object = None

    @property
    def _hive_runtime_info(self):
        # TODO why raise runtime error?
        raise RuntimeError

    @memoize
    def bind(self, run_hive):
        hive_instance = self._unbound_run_hive.bind(run_hive)
        return self._bee.bind(hive_instance)


class ResolveBee(Exportable):
    """Wraps Bee instance to resolve appropriate reference at runtime"""

    def __init__(self, bee, own_hive_object):
        self._bee = bee
        self._own_hive_object = own_hive_object
        self._hive_object_cls = get_building_hive()

    def __getattr__(self, attr):
        result = getattr(self._bee, attr)

        # Return qualified resolve bee (replace child bee hiveobject with this resolution)
        if isinstance(result, ResolveBee):
            child_bee = ResolveBee(result._bee, self)
            return child_bee

        return result

    def __repr__(self):
        return "{}->{}".format(self._own_hive_object, self._bee)

    def export(self):
        return self

    @memoize
    def getinstance(self, redirected_hive_object):
        hive_instantiator = self._own_hive_object.getinstance(redirected_hive_object)
        redirected_hive_object = hive_instantiator._hive_object
        result = self._bee.getinstance(redirected_hive_object)

        if isinstance(result, Bindable):
            return BindableResolveBee(hive_instantiator, result)

        return result

    def implements(self, cls):
        return self._bee.implements(cls)

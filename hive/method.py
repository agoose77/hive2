from inspect import isclass

from .annotations import update_wrapper
from .manager import get_building_hive, memoize
from .mixins import Bindable, Callable, Exportable, Nameable


class Method(Bindable, Callable, Exportable, Nameable):
    """Exportable interface to instance methods of bind classes"""

    def __init__(self, builder_cls, func):
        assert callable(func), func
        assert isclass(builder_cls), builder_cls

        self._builder_cls = builder_cls
        self._func = func
        self._hive_object_cls = get_building_hive()

        update_wrapper(self, func)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._func.__qualname__)

    @memoize
    def bind(self, run_hive):
        cls = self._builder_cls
        instance = run_hive._hive_build_class_to_instance[cls]

        return self._func.__get__(instance)

    def export(self):
        return self

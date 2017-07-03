from inspect import isclass, isfunction

from .annotations import update_wrapper
from .manager import memoize
from .interfaces import Bindable, Callable, Exportable, Nameable


class Method(Bindable, Callable, Exportable, Nameable):
    """Exportable interface to instance methods of bind classes"""

    def __init__(self, builder_cls, method):
        assert isfunction(method), method
        assert isclass(builder_cls), builder_cls

        self._builder_cls = builder_cls
        self._method = method

        update_wrapper(self, method)

        super().__init__()

    @memoize
    def bind(self, run_hive):
        cls = self._builder_cls
        instance = run_hive._hive_build_class_to_instance[cls]

        return self._method.__get__(instance)

    def export(self):
        return self

    def __repr__(self):
        return "Method({!r})".format(self._builder_cls, self._method)

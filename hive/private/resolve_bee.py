from hive.manager import memoize, ModeFactory
from hive.interfaces import Exportable, Nameable


class BindableResolveBee(Nameable):
    def __init__(self, unbound_run_hive, bee):
        super().__init__()

        self._bee = bee
        self._unbound_run_hive = unbound_run_hive

        # Support ResolveBees used for hive_objects
        self._hive_object = getattr(bee, '._hive_object', None)

    @property
    def _hive_runtime_aliases(self):
        # TODO why raise runtime error?
        raise RuntimeError

    def bind(self, run_hive):
        hive_instance = self._unbound_run_hive.bind(run_hive)
        return self._bee.bind(hive_instance)


class ResolveBee(Exportable):
    """Implements support for connecting between public of different HiveObjects 
    (resolving the getinstance & bind methods)
    """

    def __init__(self, bee, defining_hive_object):
        self._bee = bee
        self._defining_hive_object = defining_hive_object

        super().__init__()

    def __getattr__(self, attr):
        result = getattr(self._bee, attr)

        # Return qualified resolve bee (replace child bee hiveobject with this resolution)
        if isinstance(result, ResolveBee):
            # NOTE here we can return unique ResolveBees for the same attribute
            # This should be acceptable as the getinstance method does not need to be memoized
            child_bee = ResolveBee(result._bee, self)
            return child_bee

        return result

    def __repr__(self):
        return "RB[{}]{}".format(self._defining_hive_object.__class__.__name__, self._bee)

    def export(self):
        return self

    def bind(self, containing_instance):
        """Return a runtime instance of the wrapped Bee.
        
        :param redirected_hive_object: TODO
        """ # TODO
        # Hive instance to which the ResolveBee belongs
        run_hive = self._defining_hive_object.bind(containing_instance)
        return self._bee.bind(run_hive)

    def implements(self, cls):
        return self._bee.implements(cls)


class DescriptorResolveBee(ResolveBee):

    def __get__(self, instance, owner):
        return self._bee.__get__(instance, owner)

    def __set__(self, instance, value):
        return self._bee.__set__(instance, value)

    def __delete__(self, instance):
        return self._bee.__delete_(instance)

resolve_bee = ModeFactory("hive.resolve_bee", build=ResolveBee)
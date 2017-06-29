from .manager import memoize, ModeFactory
from .protocols import Bindable, Exportable, Nameable


class BindableResolveBee(Bindable, Nameable):
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
    """Implements support for connecting between bees of different HiveObjects 
    (resolving the getinstance & bind methods)
    """

    def __init__(self, bee, own_hive_object):
        self._bee = bee
        self._own_hive_object = own_hive_object

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
        return "[{}]{}".format(self._own_hive_object.__class__.__name__, self._bee)

    def export(self):
        return self

    def getinstance(self, redirected_hive_object):
        """Return a runtime instance of the wrapped Bee.
        
        :param redirected_hive_object: TODO
        """ # TODO

        # Hive instance to which the ResolveBee belongs
        hive_instantiator = self._own_hive_object.getinstance(redirected_hive_object)
        redirected_hive_object = hive_instantiator._hive_object
        result = self._bee.getinstance(redirected_hive_object)

        # If the resulting bee is Bindable, we must resolve this later too!
        if isinstance(result, Bindable):
            return BindableResolveBee(hive_instantiator, result)

        return result

    def implements(self, cls):
        return self._bee.implements(cls)


resolve_bee = ModeFactory("hive.resolve_bee", build=ResolveBee)
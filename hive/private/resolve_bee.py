from hive.interfaces import Exportable, Nameable, Bee


class BindableResolveBee(Nameable):
    def __init__(self, unbound_run_hive, bee):
        super().__init__()

        self._bee = bee
        self._unbound_run_hive = unbound_run_hive

        # Support ResolveBees used for hive_objects
        self._hive_object = getattr(bee, '_hive_object', None)

    @property
    def _hive_runtime_aliases(self):
        # TODO why raise runtime error?
        raise RuntimeError

    def bind(self, run_hive):
        hive_instance = self._unbound_run_hive.bind(run_hive)
        return self._bee.bind(hive_instance)


class ResolveBee(Bee, Exportable):
    """Implements support for connecting between public of different HiveObjects 
    (resolving the getinstance & bind methods)
    """

    _hive_parent_hive_object_class = None

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
        return "{}<{}>".format(self._bee, self._defining_hive_object.__class__.__name__)

    def bind(self, containing_instance):
        """Return a runtime instance of the wrapped BeeBase.
        
        :param redirected_hive_object: TODO
        """  # TODO
        # Hive instance to which the ResolveBee belongs
        run_hive = self._defining_hive_object.bind(containing_instance)
        return self._bee.bind(run_hive)

    def implements(self, cls):
        return self._bee.implements(cls)

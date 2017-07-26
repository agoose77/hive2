from ..interfaces import Exportable, Bee, BeeBase

from typing import Type


class ResolveBee(BeeBase, Exportable):
    """Implements support for connecting between public bees of different HiveObjects 
    (resolving the bind method).
    
    Overrides __instancecheck__ to support builder-bee type checks
    """
    def __init__(self, bee: Bee, defining_hive_object: 'HiveObject'):
        self._bee = bee
        self._defining_hive_object = defining_hive_object

        super().__init__()

    def __getattr__(self, attr):
        result = getattr(self._bee, attr)

        # Return qualified resolve bee (replace child bee hiveobject with this resolution)
        if isinstance(result, self.__class__):
            # NOTE here we can return unique ResolveBees for the same attribute
            # This should be acceptable as the getinstance method does not need to be memoized
            child_bee = ResolveBee(result._bee, self)
            return child_bee

        return result

    def __instancecheck__(self, instance):
        return isinstance(self._bee, instance)

    def __repr__(self):
        return "{}<{}>".format(self._bee, self._defining_hive_object.__class__.__name__)

    def bind(self, containing_instance) -> Bee:
        """Return a runtime instance of the wrapped BeeBase.
        
        :param redirected_hive_object: TODO
        """  # TODO
        # Hive instance to which the ResolveBee belongs
        run_hive = self._defining_hive_object.bind(containing_instance)
        return self._bee.bind(run_hive)

    def implements(self, cls: Type) -> bool:
        return self._bee.implements(cls)

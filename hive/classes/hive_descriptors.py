from weakref import WeakKeyDictionary


class HiveDescriptor:
    """Hive descriptor interface to Python descriptor protocol"""
    def __init__(self, bee, instance_is_internal=False):
        """Initialiser for HiveDescriptor

        :param bee: Descriptor BeeBase instance
        :param instance_is_internal: whether to expect run hive or internal hive in descriptor magic methods
        """
        self._descriptor_bee = bee
        self._instance_is_internal = instance_is_internal
        self._run_hive_to_getter = WeakKeyDictionary()
        self._run_hive_to_setter = WeakKeyDictionary()

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return self._run_hive_to_getter[instance]()

        except KeyError:
            if self._instance_is_internal:
                bound_bee = self._descriptor_bee.bind(instance._run_hive)
            else:
                bound_bee = self._descriptor_bee.bind(instance)

            getter = self._run_hive_to_getter[instance] = bound_bee._hive_descriptor_get
            return getter()

    def __set__(self, instance, value):
        try:
            self._run_hive_to_setter[instance](value)

        except KeyError:
            if self._instance_is_internal:
                bound_bee = self._descriptor_bee.bind(instance._run_hive)
            else:
                bound_bee = self._descriptor_bee.bind(instance)

            setter = self._run_hive_to_setter[instance] = bound_bee._hive_descriptor_set
            setter(value)

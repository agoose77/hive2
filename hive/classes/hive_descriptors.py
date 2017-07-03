from weakref import WeakKeyDictionary


class HiveDescriptorProxy:
    def __init__(self, bee, internal=False):
        self._descriptor_bee = bee
        self._run_hive_to_getter = WeakKeyDictionary()
        self._run_hive_to_setter = WeakKeyDictionary()
        self._internal = internal

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return self._run_hive_to_getter[instance]()

        except KeyError:
            if self._internal:
                bound_bee = self._descriptor_bee.bind(instance._run_hive)
            else:
                bound_bee = self._descriptor_bee.bind(instance)

            getter = self._run_hive_to_getter[instance] = bound_bee._hive_descriptor_get
            return getter()

    def __set__(self, instance, value):
        try:
            self._run_hive_to_setter[instance](value)

        except KeyError:
            if self._internal:
                bound_bee = self._descriptor_bee.bind(instance._run_hive)
            else:
                bound_bee = self._descriptor_bee.bind(instance)

            setter = self._run_hive_to_g = setter[instance] = bound_bee._hive_descriptor_set
            setter(value)

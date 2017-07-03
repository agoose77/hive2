from weakref import WeakKeyDictionary
from functools import wraps


def memoize(func):
    """Memoizing decorator

    Cache function call results for similar arguments
    """
    func_instance_cache = WeakKeyDictionary()

    @wraps(func)
    def wrapper(self, *args):
        try:
            results_cache = func_instance_cache[self]

        except KeyError:
            results_cache = func_instance_cache[self] = {}

        try:
            return results_cache[args]

        except KeyError:
            result = results_cache[args] = func(self, *args)
            return result

    return wrapper


class MemoProperty:

    def __init__(self, fget):
        self.fget = fget
        self._memo_dict = WeakKeyDictionary()

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        try:
            return self._memo_dict[instance]

        except KeyError:
            self._memo_dict[instance] = result = self.fget(instance)()
            return result


def memo_property(fget):
    return MemoProperty(fget)

"""Classes which follow the Bee protocol

The following rules ensure that a Bee remains a Bee under the Bee protocols of getinstance, bind and export
*  Bee.getinstance must return a Bee instance
*  Bindable.bind must return a Bee instance
*  Exportable.export must return a Bee instance

Exportable.export() can only be called on the result of Bee.getinstance
Bindable.bind() can only be called on the result of Bee.getinstance() or Exportable.export()

Hence, Bindable and Exportable must be Bees
"""

from abc import ABC, abstractmethod
from logging import getLogger
from ..contexts import get_building_hive


logger = getLogger(__name__)


class Bee:
    # TODO: resolve method for arguments that are bees (returns a new HiveBee class?)

    _parent_hive_object_class = None

    def __init__(self):
        self._parent_hive_object_class = get_building_hive()
        if get_building_hive() is None:
            logger.warning("Building hive is none for {}, is this the root hive?".format(self))

    # TODO remove impleemtsn
    def implements(self, cls):
        """Return True if the Bee returned by getinstance will implement a given class.
        
        Required to support inspection of runtime-bees
        
        :param cls: class
        """
        return isinstance(self, cls)

    def bind(self, runtime_hive):
        return self

    def getinstance(self, hive_object):
        return self


class Bindable(Bee):
    pass


class Exportable(Bee, ABC):

    def export(self):
        raise NotImplementedError

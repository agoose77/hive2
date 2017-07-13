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
from typing import Type

from ..contexts import get_building_hive

logger = getLogger(__name__)


class Bee(ABC):
    # TODO: resolve method for arguments that are public (returns a new HiveBee class?)

    @property
    @abstractmethod
    def _hive_parent_hive_object_class(self) -> Type:
        pass

    def implements(self, cls: Type) -> bool:
        """Return True if the BeeBase returned by getinstance will implement a given class.
        
        Required to support inspection of runtime-public
        
        :param cls: class to test against
        """
        return isinstance(self, cls)

    def bind(self, runtime_hive):
        return self


class BeeBase(Bee):
    _hive_parent_hive_object_class = None

    def __init__(self):
        self._hive_parent_hive_object_class = get_building_hive()
        if get_building_hive() is None:
            logger.warning("Building hive is none for {}, is this the root hive?".format(self))


class Exportable:
    pass

from ..functional.triggerfunc import TriggerFuncBuilder as FunctionalTriggerFuncBuilder, TriggerFunc as FunctionalTriggerFunc
from ..interfaces import Exportable
from .interfaces import TriggerableMixin


class TriggerFuncRuntime(FunctionalTriggerFunc, Exportable, TriggerableMixin):
    pass


class TriggerFuncBuilder(FunctionalTriggerFuncBuilder, Exportable, TriggerableMixin):
    runtime_cls = TriggerFuncRuntime

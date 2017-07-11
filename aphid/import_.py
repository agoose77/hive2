from os.path import dirname
from importlib import import_module


import hive
import hive_editor


class ImportClass:

    def __init__(self):
        self._hive = hive.get_run_hive()

        self.import_path = None
        self.module = None

    def do_import_from_path(self):
        # Find first runtime info object and assume is the only one required
        runtime_aliases = self._hive._hive_runtime_aliases
        if not runtime_aliases:
            raise RuntimeError("This hive does not have any runtime aliases (it is not nested within another HiveObject)")

        # Find first hive to embed this hive (TODO maybe iterate here)
        first_runtime_info = next(iter(runtime_aliases))
        parent = first_runtime_info.parent_ref()
        container_parent_class = parent._hive_object._hive_parent_class

        hook = hive_editor.get_hook()

        # Find the loader result of the hive in which this hive is embedded (to find the __package__)
        try:
            loader_result = hook.find_loader_result_for_class(container_parent_class)

        except ValueError:
            package = None

        else:
            package = loader_result.module.__package__

        self.module = import_module(self.import_path, package=package)


def build_import(cls, i, ex, args):
    """Interface to python import mechanism, with respect to editor project path"""
    i.import_path = hive.property(cls, "import_path", 'str')
    i.pull_import_path = hive.pull_in(i.import_path)
    ex.import_path = hive.antenna(i.pull_import_path)

    i.do_import = hive.triggerable(cls.do_import_from_path)

    i.module = hive.property(cls, "module", "module")
    i.pull_module = hive.pull_out(i.module)
    ex.module = hive.output(i.pull_module)

    hive.trigger(i.pull_module, i.pull_import_path, pretrigger=True)
    hive.trigger(i.pull_module, i.do_import, pretrigger=True)


Import = hive.hive("Import", build_import, drone_class=ImportClass)


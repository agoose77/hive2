from os.path import dirname
from importlib import import_module


import hive
import hive2_gui


class ImportClass:

    def __init__(self):
        self.import_path = None
        self.module = None

    def do_import_from_path(self):
        # Find first runtime info object and assume is the only one required
        runtime_aliases = hive.external(self)._hive_runtime_aliases # TODO
        if not runtime_aliases:
            raise RuntimeError("This hive does not have any runtime aliases (not nested within another HiveObject)")

        # Find first hive to embed this hive
        first_runtime_info = next(iter(runtime_aliases))
        parent = first_runtime_info.parent_ref()
        container_parent_class = parent._hive_object._hive_parent_class

        hook = hive2_gui.get_hook()

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
    ex.import_path = i.import_path.pull_in

    i.do_import = cls.do_import_from_path

    i.module = hive.property(cls, "module", "module")
    ex.module = i.module.pull_out

    i.module.pull_in.pre_triggered.connect(i.import_path.pull_in.trigger)
    i.module.pull_in.pre_triggered.connect(i.do_import.trigger)


Import = hive.hive("Import", build_import, drone_class=ImportClass)


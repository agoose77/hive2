import hive
from importlib import import_module


def do_import_from_path(i, ex):
    i.module.value = import_module(i.import_path.value)


def build_import(i, ex, args):
    """Interface to python import mechanism"""
    i.do_import = hive.modifier(do_import_from_path)

    i.import_path = hive.attribute("str")
    ex.import_path = i.import_path.pull_in

    i.module = hive.attribute("module")
    ex.module = i.module.pull_out

    i.module.pull_out.pre_triggered.connect(i.import_path.pull_in.trigger,
                                               i.do_import.trigger)


Import = hive.hive("Import", build_import)

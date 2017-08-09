import ast
import hive
import math


class VariableRecorder(ast.NodeVisitor):

    def __init__(self):
        super().__init__()

        self.undefined_ids = []

    def visit_Name(self, node):
        if not hasattr(math, node.id):
            self.undefined_ids.append(node.id)


def create_func(expression, names):
    declaration = """
from math import *
def func(i, ex):
    {}
    i.result.value = ({})"""

    declarations = "\n    ".join(["{0}=i.{0}.property".format(name) for name in names])
    configure_func = declaration.format(declarations, expression)

    namespace = {}
    print(configure_func)
    exec(configure_func, namespace)
    func = namespace['func']

    return func


def configure_expression(meta_args):
    meta_args.expression = hive.parameter("str", "")
    meta_args.result_type = hive.parameter('str', "int")


def build_expression(i, ex, args, meta_args):
    """Evaluate Python expression and store result"""
    ast_node = ast.parse(meta_args.expression, mode='eval')

    # Visit AST and find variable names
    visitor = VariableRecorder()
    visitor.visit(ast_node)
    variable_names = visitor.undefined_ids

    i.result = hive.attribute(meta_args.result_type)
    ex.result = i.result.pull_out

    for name in variable_names:
        attribute = hive.attribute(meta_args.result_type)
        setattr(i, name, attribute)
        setattr(ex, name, attribute.pull_in)

        i.result.pull_out.before.connect(attribute.pull_in.trigger)

    func = create_func(meta_args.expression, variable_names)
    i.modifier = hive.modifier(func)
    i.result.pull_out.before.connect(i.modifier.trigger)


Expression = hive.dyna_hive("Expression", build_expression, configurer=configure_expression)

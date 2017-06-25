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
def func(self):
    {}
    self._result = {}"""

    declarations = "\n    ".join(["{0}=self._{0}".format(name) for name in names])
    declare_func = declaration.format(declarations, expression)

    namespace = {}
    exec(declare_func, namespace)
    func = namespace['func']

    return func


def declare_expression(meta_args):
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
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    for name in variable_names:
        attribute = hive.attribute(meta_args.result_type)
        setattr(i, name, attribute)
        pull_in = hive.pull_in(attribute)
        setattr(ex, name, hive.antenna(pull_in))

        hive.trigger(i.pull_result, pull_in, pretrigger=True)

    func = create_func(meta_args.expression, variable_names)
    i.modifier = hive.modifier(func)
    hive.trigger(i.pull_result, i.modifier, pretrigger=True)


Expression = hive.dyna_hive("Expression", build_expression, declarator=declare_expression)

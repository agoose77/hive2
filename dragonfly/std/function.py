import ast
from collections import OrderedDict

import hive


def declare_func(meta_args):
    meta_args.definition = hive.parameter("str.code")


class ReturnVisitor(ast.NodeVisitor):
    """Find return statement in top level function defintion (do not recurse)"""

    def __init__(self):
        self.return_occurs = False

    def visit_Return(self, node):
        self.return_occurs = True

    def visit_FunctionDef(self, node):
        pass


function_no_return = object()


class FunctionDefinitionVisitor(ast.NodeVisitor):
    """Visit module and find first FunctionDefinition"""

    def __init__(self):
        self.name = None
        self.antennae = OrderedDict()
        self.output_type_name = function_no_return
        self._args = OrderedDict()

    def visit_arg(self, node):
        self._args[node.arg] = node.annotation

    def visit_FunctionDef(self, node):
        self.name = node.name
        self.visit(node.args)

        # Get arg info from visiting the ast.arg objects to avoid handling each arg type here
        defaults = OrderedDict([(a, d) for a, d in zip(reversed(self._args.keys()), reversed(node.args.defaults))])
        self.antennae = self._get_antennae(self._args, defaults)

        return_visitor = ReturnVisitor()
        for child in node.body:
            return_visitor.visit(child)

        returns = return_visitor.return_occurs
        return_type_name = self._annotation_to_type_name(node.returns)

        if not returns:
            self.output_type_name = function_no_return
        else:
            self.output_type_name = return_type_name

    def _annotation_to_type_name(self, annotation):
        """Produce type name from argument annotation
        
        :param annotation: annotation node
        """
        if isinstance(annotation, ast.Str):
            return annotation.s
        elif isinstance(annotation, ast.Name):
            return annotation.id
        elif annotation is None:
            return None
        else:
            raise ValueError

    def _get_antennae(self, args, defaults):
        """Build OrderedDict of antennae names to type names, defaults
        
        :param args: OrderedDict of arg name to annotation
        :param defaults: dict mapping arg name to default value (if present)
        """
        antennae = OrderedDict()

        for arg, annotation in args.items():
            if arg in defaults:
                default_ast = defaults[arg]
                default = ast.literal_eval(default_ast)
            else:
                default = None

            type_name = self._annotation_to_type_name(annotation)

            antennae[arg] = (type_name, default)

        return antennae


modifier_str = """
def modifier(self):
    self._pull_all_inputs()
    result = {function_call_str}
    {result_body}
"""

result_str = """
    self._result = result
    self.result.push()
"""


def build_func(i, ex, args, meta_args):
    """Define callable object from expression"""
    # Get AST and parse ags
    ast_node = ast.parse(meta_args.definition, mode='exec')
    assert isinstance(ast_node, ast.Module)
    assert len(ast_node.body) == 1
    func_def_ast = ast_node.body[0]
    assert isinstance(func_def_ast, ast.FunctionDef)

    visitor = FunctionDefinitionVisitor()
    visitor.visit(ast_node)

    # Build the function itself
    user_namespace = {}
    exec(meta_args.definition, user_namespace)
    user_func = user_namespace[func_def_ast.name]

    has_return = visitor.output_type_name is not function_no_return

    # Define modifier source code (here, we will lookup the "user_func" name later)
    function_call_str = "user_func({})".format(", ".join(["self._{}".format(a) for a in visitor.antennae]))
    result_body = result_str if has_return else ""
    modifier_decl = modifier_str.format(function_call_str=function_call_str,
                                        result_body=result_body)

    # Build modifier function
    namespace = {'user_func': user_func}
    exec(modifier_decl, namespace)
    modifier_func = namespace['modifier']

    # Create modifier api_bees
    i.modifier = hive.modifier(modifier_func)
    ex.trigger = hive.entry(i.modifier)

    i.pull_all_inputs = hive.triggerfunc()

    # Create IO pins
    for arg, (type_name, default) in visitor.antennae.items():
        attr = hive.variable(type_name, start_value=default)
        setattr(i, arg, attr)
        pull_in = hive.pull_in(attr)
        setattr(ex, arg, hive.antenna(pull_in))
        hive.trigger(i.pull_all_inputs, pull_in, pretrigger=True)

    if has_return:
        result_name = 'result'
        attr = hive.variable(visitor.output_type_name)
        setattr(i, result_name, attr)
        push_out = hive.push_out(attr)
        setattr(ex, result_name, hive.output(push_out))


Function = hive.dyna_hive("Function", build_func, declarator=declare_func)

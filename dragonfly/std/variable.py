import hive


def declare_variable(meta_args):
    meta_args.data_type = hive.parameter("str", "int")
    meta_args.advanced = hive.parameter("bool", False)


def build_variable(i, ex, args, meta_args):
    """Simple value-holding hive"""
    args.start_value = hive.parameter(meta_args.data_type)
    ex.value = hive.variable(meta_args.data_type, args.start_value)

    i.pull_value = hive.pull_out(ex.value)
    ex.value_out = hive.output(i.pull_value)

    i.push_value = hive.push_in(ex.value)
    ex.value_in = hive.antenna(i.push_value)

    if meta_args.advanced:
        i.pre_output = hive.triggerfunc()
        ex.pre_output = hive.hook(i.pre_output)

        i.do_pre_output = hive.triggerable(i.pre_output)
        hive.trigger(i.pull_value, i.do_pre_output, pretrigger=True)

Variable = hive.dyna_hive("Variable", build_variable, declarator=declare_variable)

# Helpers
_MetaVariable = Variable.extend("MetaVariable", is_dyna_hive=False)
VariableStr = _MetaVariable(data_type='str')
VariableInt = _MetaVariable(data_type='int')
VariableFloat = _MetaVariable(data_type='float')
VariableBool = _MetaVariable(data_type='bool')

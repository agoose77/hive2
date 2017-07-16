import hive


def configure_variable(meta_args):
    meta_args.data_type = hive.parameter("str", "int")
    meta_args.advanced = hive.parameter("bool", False)


def build_variable(i, ex, args, meta_args):
    """Simple value-holding hive"""
    args.start_value = hive.parameter(meta_args.data_type)
    i.value = hive.attribute(meta_args.data_type, args.start_value)

    ex.value = i.value.proxy()
    ex.value_out = i.value.pull_out
    ex.value_in = i.value.push_in

    if meta_args.advanced:
        i.pre_output = hive.modifier()
        i.value.pull_out.pre_pushed.connect(i.pre_output.pushed)

        ex.pre_output = i.pre_output.pushed

Variable = hive.dyna_hive("BuilderVariable", build_variable, configurer=configure_variable)

# Helpers
_MetaVariable = Variable.extend("MetaVariable", is_dyna_hive=False)
VariableStr = _MetaVariable(data_type='str')
VariableInt = _MetaVariable(data_type='int')
VariableFloat = _MetaVariable(data_type='float')
VariableBool = _MetaVariable(data_type='bool')

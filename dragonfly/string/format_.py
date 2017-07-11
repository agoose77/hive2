import string

import hive


def declare_format(meta_args):
    meta_args.format_string = hive.parameter("str", "{}")


# TODO make non-attr names editable
def build_format(i, ex, args, meta_args):
    """Interface to Python string value formatting"""
    formatter = string.Formatter()
    format_string = meta_args.format_string
    fields = list(formatter.parse(format_string))

    kwarg_fields = []
    indexed_fields = []

    i.result = hive.attribute('str')
    i.result_out = hive.pull_out(i.result)

    for index, field in enumerate(fields):
        literal_text = field[1]

        if literal_text is None:
            continue

        if not literal_text.isidentifier():
            field_name = "field_{}".format(index)
            indexed_fields.append(field_name)

        else:
            field_name = literal_text
            kwarg_fields.append(field_name)

        # Create IO
        attr = hive.attribute()
        setattr(i, field_name, attr)

        in_attr = hive.pull_in(attr)
        setattr(i, "{}_in".format(field_name), in_attr)

        setattr(ex, field_name, hive.antenna(in_attr))
        hive.trigger(i.result_out, in_attr, pretrigger=True)

    ex.result = hive.output(i.result_out)

    def do_format(self):
        args = [getattr(self, "_{}".format(attr_name)) for attr_name in indexed_fields]
        kwargs = {attr_name: getattr(self, "_{}".format(attr_name)) for attr_name in kwarg_fields}
        self._result = formatter.format(format_string, *args, **kwargs)

    i.func = hive.modifier(do_format)
    hive.trigger(i.result_out, i.func, pretrigger=True)


Format = hive.dyna_hive("Format", build_format, declarator=declare_format)

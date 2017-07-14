import string

import hive


def configure_format(meta_args):
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
    ex.result = i.result.pull_out

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
        setattr(ex, field_name, attr.pull_in)
        i.result_out.pre_pushed.connect(attr.pull_in.trigger)

    def do_format(i, ex):
        args = [getattr(i, "{}.property".format(attr_name)) for attr_name in indexed_fields]
        kwargs = {attr_name: getattr(i, "{}.property".format(attr_name)) for attr_name in kwarg_fields}
        i.result.value = formatter.format(format_string, *args, **kwargs)

    i.do_format = hive.modifier(do_format)
    i.result.pull_out.pre_pushed.connect(i.do_format.trigger)


Format = hive.dyna_hive("Format", build_format, configurer=configure_format)

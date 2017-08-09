import hive


def create_generator_func(generator_string):
    declaration = """
def generator():
    {}
    """

    body = generator_string.replace("\n", "\n    ")
    declaration_string = declaration.format(body)
    exec(declaration_string, locals(), globals())

    return generator


def on_new_generator(self):
    generator_func = create_generator_func(self.generator_body)
    self.generator = generator_func()


def build_generator(i, ex, args):
    """Define and instantiate a new generator when pulled"""
    args.generator_body = hive.parameter(("str", "code"))

    ex.generator = hive.attribute()
    ex.generator_body = hive.attribute(("str", "code"), args.generator_body)

    i.create_generator = hive.modifier(on_new_generator)

    i.generator_out = hive.pull_out(ex.generator)
    ex.generator_out = hive.output(i.generator_out)

    hive.trigger(i.generator_out, i.create_generator, pretrigger=True)


Generator = hive.hive("Generator", build_generator)
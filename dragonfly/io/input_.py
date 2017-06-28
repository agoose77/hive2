import hive


def build_input(i, ex, args):
    """Get input from Python stdin"""
    args.message = hive.parameter("str", "")
    ex.message = hive.variable("str", args.message)

    i.message_in = hive.push_in(ex.message)
    ex.message_in = hive.antenna(i.message_in)

    ex.value = hive.variable("str")
    i.value_out = hive.pull_out(ex.value)
    ex.value_out = hive.output(i.value_out)

    def get_input(self):
        self.value = input(self.message)

    i.get_input = hive.modifier(get_input)
    hive.trigger(i.value_out, i.get_input, pretrigger=True)


Input = hive.hive("Input", build_input)

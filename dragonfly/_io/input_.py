import hive


def get_input(i, ex):
    i.value.value = input(i.message.value)

def build_input(i, ex, args):
    """Get input from Python stdin"""
    args.message = hive.parameter("str", "")
    i.message = hive.attribute("str", args.message)

    ex.message_in = i.message.push_in

    i.value = hive.attribute("str")
    ex.value = i.value.pull_out

    i.get_input = hive.modifier(get_input)
    i.value.pull_out.before.connect(i.get_input.trigger)


Input = hive.hive("Input", build_input)

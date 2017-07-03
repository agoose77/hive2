import hive


def some_func(i, ex):
    pass


def build(i, ex, args):
    i.func = hive.function(some_func)
    ex.do = i.func._trigger
    i.func.triggered.connect(i.update_score)

    hive.connect(i.func, i.update_score)
    # OR

    i.value = hive.attribute("int")
    i.value.push_in.pretriggers(i.func)
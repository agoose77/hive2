import hive



class DroneClass:
    @property
    def foo(self):
        return 'x'

    def print_foo(self):
        print("Printing foo", self.foo)

    def set_plugin(self, p):
        print("Plugin", p)
        p()


def on_attr_updated(i, ex):
    print("attr updated!", i.attr.value)


def on_attr_updated_pre(i, ex):
    print("attr pre-updated!", i.attr.value)


def on_attr_pulled_in(i, ex):
    print("attr pull invoked!")


def on_attr_pulled_out(i, ex):
    print("attr pulled out!")


def do_pull(i, ex):
    print("invoking pull of attr")


def build(cls, i, ex, args):
    i.attr = hive.attribute("int")

    i.pre_updated = hive.modifier(on_attr_updated_pre)
    i.attr.pre_updated.connect(i.pre_updated.trigger)

    i.updated = hive.modifier(on_attr_updated)
    i.attr.updated.connect(i.updated.trigger)

    i.on_attr_pulled_out = hive.modifier(on_attr_pulled_out)
    i.attr.pull_out.triggered.connect(i.on_attr_pulled_out.trigger)

    i.on_attr_pulled_in = hive.modifier(on_attr_pulled_in)
    i.attr.pull_in.triggered.connect(i.on_attr_pulled_in.trigger)

    i.do_pull = hive.modifier(do_pull)
    i.do_pull.triggered.connect(i.attr.pull_in.trigger)

    ex.foo = cls.foo.property()

    ex.value = i.attr.property(hive.WRITE)

    ex.do_pull = i.do_pull.trigger
    ex.value_in = i.attr.pull_in

    ex.value_out = i.attr.pull_out
    ex.print_foo = cls.print_foo.trigger

    ex.plug = i.updated.trigger.plugin()
    # ex.sock = hive.socket(cls.set_plugin)


H = hive.hive("build", build, drone_class=DroneClass)
h = H()
h2 = H()

hive.connect(h,h2)
# h.value_out.connect(h2.value_in)

h.value = 99
h2.value = 10

print(h2.value_out())

h2.do_pull()
print(h2.value_out())

print(h2.plug.plugin()())

# print("START")
#
# attr = attribute("int", 99)
# attr.pull_out.connect(h.value_in)
# print(h.do_pull())
# print(h.foo)
# h.print_foo()
#
#
# def get_plug(p):
#     print("Got plug", p)
#     p()
#
#
# s = socket(get_plug)
# h.plug.connect(s)
# h.value = 9
# print(h.do_pull())
# print(h.value)


# from time import clock as monotonic
# def test(n,x):
#     s = monotonic()
#     for i in range(n):
#         h.value# = x
#         # h.push_value.push(x)
#
#     print("took", monotonic()-s)
#
# from time import clock as monotonic
# def testp(n,x):
#     s = monotonic()
#     for i in range(n):
#         # h.value = x
#         h.pull_value.pull()
#
#     print("took", monotonic()-s)
#
# def test2(n,x):
#     ex = h
#     i = ex._hive_i
#     ho=type("",(),{})()
#     ho.value=x
#     s = monotonic()
#     for i in range(n):
#         ho.value# = x
#         debug(i,ex)
#     print("took", monotonic()-s)
#
# n=100000
# x = 100
# if 1:
#     test(n,x)
#     testp(n,x)
#     test2(n,x)
# else:
#     from cProfile import runctx
#     runctx("test(n,x)",locals(),globals())

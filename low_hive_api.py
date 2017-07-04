import hive
from hive.high_level.attribute import attribute
from hive.high_level.function import function

# attr = attribute("int")
#
# def debug():
#     print("Updated!", attr.value)
#
# trig = function(debug)
# attr.before_update.connect(trig.trigger)
# attr.after_update.connect(trig.trigger)
#
# attr.value = 12

from hive.functional.stateful_descriptor import READ_WRITE, READ, WRITE

class DroneClass:

    @property
    def foo(self):
        return 'x'

    def print_foo(self):
        print("Printing foo", self.foo)


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

def build(cls, i,ex,args):
    i.attr = attribute("int")

    i.before_updated = function(on_attr_updated_pre)
    i.attr.before_updated.connect(i.before_updated.trigger)

    i.updated = function(on_attr_updated)
    i.attr.updated.connect(i.updated.trigger)

    i.on_attr_pulled_out = function(on_attr_pulled_out)
    i.attr.pull_out.triggered.connect(i.on_attr_pulled_out.trigger)

    i.on_attr_pulled_in = function(on_attr_pulled_in)
    i.attr.pull_in.triggered.connect(i.on_attr_pulled_in.trigger)

    i.do_pull = function(do_pull)
    i.do_pull.triggered.connect(i.attr.pull_in.trigger)

    ex.foo = cls.foo.property()

    ex.value = i.attr.property(WRITE)

    ex.do_pull = i.do_pull.trigger
    ex.value_in = i.attr.pull_in

    ex.value_out = i.attr.pull_out
    ex.print_foo = cls.print_foo.trigger


H = hive.hive("build",build, drone_cls=DroneClass)
h = H()
print("START")

attr = attribute("int", 99)
attr.pull_out.connect(h.value_in)
print(h.do_pull())
print(h.foo)
h.print_foo()
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
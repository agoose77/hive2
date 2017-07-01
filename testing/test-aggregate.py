import hive


def build_a(i, ex, args):
    i.mod_a = hive.modifier(lambda self: print("A modifier()"))
    ex.a = hive.entry(i.mod_a)


def build_b(i, ex, args):
    i.mod_b = hive.modifier(lambda self: print("B modifier()"))
    ex.b = hive.entry(i.mod_b)


A = hive.hive("A", build_a)
B = hive.hive("B", build_b)


def build_c(i, ex, args):
    i.mod_c = hive.modifier(lambda self: self._mod_a() or self._mod_b())
    ex.c = hive.entry(i.mod_c)

C = hive.hive("C", build_c, bases=(A, B))
D = C.extend("D")

c = C()
print("c.a()")
c.a()

print("\nc.b()")
c.b()

print("\nc.C()")
c.c()

d = D()
print("\nd.c()")
d.c()
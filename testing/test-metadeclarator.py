# Begin Boilerplate
from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive
# End Boilerplate


def configure_dog(meta_args):
    print("Invoked Declarator")
    meta_args.puppies = hive.parameter("int", 1)
    

def build_dog(i, ex, args, meta_args):
    print("Invoked Builder")
    print(args)
    
    args.name = hive.parameter("str")
    ex.name = hive.attribute("str", args.name)

    for ix in range(meta_args.puppies):
        mod = hive.modifier(lambda h: print("Puppy {} barked".format(h.name)))
        setattr(i, "mod_{}".format(ix), mod)
        setattr(ex, "bark_{}".format(ix), hive.entry(mod))


def test_dyna():
    DynaDogHive = hive.dyna_hive("Dog", build_dog, configure_dog)

    print("\n#1: MetaArg=2, Arg='Jack'")
    d = DynaDogHive(2, "Jack")
    d.bark_0()
    d.bark_1()

    print("\n#2: MetaArg=1, Arg='Jill'")
    d = DynaDogHive(1, "Jill")
    d.bark_0()

    print("\n#3: MetaArg=1, Arg='Bobby'")
    d = DynaDogHive(1, "Bobby")
    d.bark_0()


def test_meta():
    MetaDogHive = hive.meta_hive("Dog", build_dog, configure_dog)

    d = MetaDogHive(2)("Jack")

    print("\n#1: MetaArg=2, Arg='Jack'")
    d.bark_0()
    d.bark_1()

    print("\n#2: MetaArg=1, Arg='Jill'")
    d = MetaDogHive(1)("Jill")
    d.bark_0()

    print("\n#3: MetaArg=1, Arg='Bobby'")
    d = MetaDogHive(1)("Bobby")
    d.bark_0()


print('-'*20)
print("Test Dyna")
print('-'*20)
test_dyna()

print('-'*20)
print("Test Meta")
print('-'*20)
test_meta()
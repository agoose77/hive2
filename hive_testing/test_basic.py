from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive as h


def ping():
    print("PING")


def pong():
    print("PONG")


#hping is a function; when called, it calls ping and then send a trigger
hping = h.triggerfunc(ping)
#hpong calls pong when it receives a trigger
hpong = h.triggerable(pong)
#hping will send its triggers to hpong
h.trigger(hping, hpong)

#hpang is a function; when called, it sends a trigger
hpang = h.triggerfunc()
#hpang will send its triggers to hpong
h.trigger(hpang, hpong)

print(1)
hping() # => PING PONG

print(2)
hpang() # => PONG


class Dog(object):

    def __init__(self, name):
        self._hive = h.get_run_hive()
        self.name = name
        self.woofs = 0

    def call(self):
        print("CALL", self.name)

    def woof(self):
        self.woofs += 1
        print("WOOF", self.name, self.woofs)
        self._hive.woofed()


def woof2(self):
    self.woofs2 += 1
    print("\n\nWOOF2", self.name, self.woofs2)


def build_dog(cls, i, ex, args):
    i.call = h.triggerfunc(cls.call)
    i.woof = h.triggerable(cls.woof)
    #h.trigger(i.call, i.woof)
    h.connect(i.call, i.woof)
    i.woof2 = h.modifier(woof2)
    i.bark = h.triggerfunc()
    h.trigger(i.bark, i.woof)    
    i.woofed = h.triggerfunc()    

    ex.woofs = h.property(cls, "woofs")
    ex.name = h.property(cls, "name")
    ex.woofs2 = h.variable(data_type="int", start_value=0)
    ex.woof = h.entry(i.woof)
    ex.woofed = h.hook(i.woofed)
    ex.bark = h.hook(i.bark)
    ex.call = h.hook(i.call)
    

dog = h.hive("dog", build_dog, Dog)

spot = dog("Spot")
spike = dog("Spike")

print(3)
print(spot.name) #=> Spot
spot.call() #=> CALL Spot WOOF Spot 1
h.connect(spot.call, spot._woof2)
spot.call() #=> CALL Spot WOOF Spot 2 WOOF2 Spot 1
print("SPOT WOOFS", spot.woofs, spot.woofs2) #=> SPOT WOOFS 2 1
print(4)
spot.bark() #=> WOOF Spot 3
print(5)
spike.call() #=> CALL Spike WOOF Spike 1
spike.call() #=> CALL Spike WOOF Spike 2
print(6)
spike.bark() #=> WOOF Spike 3


class House(object):

    def dog_comes(self):
        print("A dog comes")

    def mail(self):
        print("Mail arrives")


def build_house(cls, i, ex, args):
    i.brutus = dog("Brutus")
    i.fifi = dog("Fifi")
    
    i.dog_comes = h.triggerable(cls.dog_comes)
    h.trigger(i.brutus.call, i.dog_comes)
    
    i.mail = h.triggerfunc(cls.mail)
    h.trigger(i.mail, i.fifi.woof)
    
    ex.brutus = i.brutus
    ex.fifi = i.fifi
    ex.mail = h.hook(i.mail)
    ex.dog_comes = h.entry(i.dog_comes)


house = h.hive("House", build_house, House)

h2 = house()
print(7)
h2.mail() #=> Mail arrives; WOOF Fifi 1 
print(8)
h2.brutus.call() #=> CALL Brutus WOOF Brutus 1; A dog comes 
print(9)
h2.fifi.bark() #=> WOOF Fifi 2
print("9a")
h2.dog_comes() #=> A dog comes


def build_kennel(i, ex, args):
    i.brutus = dog("Brutus")
    i.fifi = dog("Fifi")
    #h.trigger(i.fifi.call, i.brutus.woof)
    #h.trigger(i.fifi.call, i.brutus)
    h.connect(i.fifi.call, i.brutus)
    
#underscore (_) names for brutus and fifi, since they are not in ex

kennel = h.hive("kennel", build_kennel)
k = kennel()
k2 = kennel()

print(10)
k._fifi.call() #=> CALL Fifi; WOOF Fifi 1; WOOF Brutus 1

h.connect(k._brutus.woofed, k._fifi)
#or: h.connect(k._brutus.woofed, k._fifi.woof)
#or: h.trigger(k._brutus.woofed, k._fifi.woof)
#or: h.trigger(k._brutus.woofed, k._fifi)
###or:
#try:
#    h.trigger(k._brutus, k._fifi) #TypeError: ambiguity between woofed and call
#except:
#    traceback.print_exc()    
###or:
#h.connect(k._brutus, k._fifi.woof) #TypeError: ambiguity between bark, call and woofed
#h.connect(k._brutus, k._fifi) #TypeError: ambiguity between bark-woof, call-woof and woofed-woof

print(11)
k._fifi.call() #=> CALL Fifi; WOOF Fifi 2; WOOF Brutus 2; WOOF Fifi 3
print("FIFI WOOFS", k._fifi.woofs) #FIFI WOOFS 3
k._fifi.woofs = 10
print("FIFI WOOFS", k._fifi.woofs) #FIFI WOOFS 10
print("K2 FIFI WOOFS", k2._fifi.woofs) #FIFI WOOFS 0
print(12)
k._brutus.call() #=> CALL Brutus; WOOF Brutus 3; WOOF Fifi 11
print(13)
k2._brutus.call() #=> CALL Brutus; WOOF Brutus 1
print( "END")
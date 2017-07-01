import os
import sys

currdir = os.path.split(os.path.abspath(__file__))[0]
sys.path.insert(0, currdir + "/" + "..")
import hive as h
import dragonfly

from chess.chessboard import chessboard
from direct.showbase.ShowBase import taskMgr

def pandarender():
  taskMgr.step()
  taskMgr.step()  

pandarender = h.triggerable(pandarender)
c = chessboard()

mainloop = dragonfly.mainloop(1000) #maximum 1000 frames/sec

#h.connect(mainloop, pandarender)
h.trigger(mainloop, pandarender)

commandline = dragonfly.Commandline()
h.trigger(mainloop, commandline.flush)

c.do_make_move("e2-e4")

"""
##############
#1. plugin-socket connection
h.connect(c.p_make_move, commandline.listen)
#send over the socket
commandline.send_command("e7-e5")
##############
"""

##############
#2. antenna-output connection
h.connect(commandline.command, c.make_move)

#send over the antenna
commandline.prop_command = "e7-e5"
commandline._push_command()
##############

commandline.start()

mainloop.run()

import os
currdir = os.path.split(os.path.abspath(__file__))[0]

from panda3d.core import getModelPath
getModelPath().prependPath(currdir)

from . import TutChessboard
from chesskeeper import parse_move


def unparse_move(fr, to, p_fr, p_to):
    if isinstance(p_fr, TutChessboard.Pawn):
        p = ""

    elif isinstance(p_fr, TutChessboard.King):
        p = "K"

    elif isinstance(p_fr, TutChessboard.Queen):
        p = "Q"

    elif isinstance(p_fr, TutChessboard.Rook):
        p = "R"

    elif isinstance(p_fr, TutChessboard.Bishop):
        p = "B"

    elif isinstance(p_fr, TutChessboard.Knight):
        p = "N"

    else:
        raise TypeError(p_fr)

    columns = ("a", "b", "c", "d", "e", "f", "g", "h")
    row_fr = int(fr / 8) + 1
    col_fr = columns[fr - 8 * (row_fr - 1)]
    row_to = int(to / 8) + 1
    col_to = columns[to - 8 * (row_to - 1)]
    sign = "-"

    if p_to is not None:
        sign = "x"

    if p == "" and col_fr != col_to:
        sign = "x"

    move = "%s%s%s%s%s%s" % (p, col_fr, row_fr, sign, col_to, row_to)

    # auto-promote to queen
    if len(move) == 5 and move[-1] in ("1", "8"):
        move = move + "Q"

    # castling
    if move == "Ke1-g1":
        move = "O-O"

    if move == "Ke1-c1":
        move = "O-O-O"

    if move == "Ke8-g8":
        move = "O-O"

    if move == "Ke8-c8":
        move = "O-O-O"

    return move


class pandachessboard(TutChessboard.World):

    def __init__(self):
        TutChessboard.World.__init__(self)
        self.turn = "White"

    def invalid_move(self, move):
        raise ValueError(move)

    def move(self, move):
        # default move: cause the piece to move back where it was
        raise ValueError

    def swapPieces(self, fr, to):
        move = unparse_move(fr, to, self.pieces[fr], self.pieces[to])
        try:
            self.move(move)
        except ValueError:
            # move back the piece to where it was
            if self.pieces[fr] is not None:
                self.pieces[fr].obj.setPos(TutChessboard.SquarePos(fr))
            self.invalid_move(move)

    def make_move(self, move):
        start, dest, special = parse_move(move, self.turn)
        start = 8 * start[1] + start[0]
        dest = 8 * dest[1] + dest[0]

        def remove_(dest):
            if dest in self.pieces and self.pieces[dest] != None and self.pieces[dest].obj != None:
                self.pieces[dest].obj.hide()
                self.pieces[dest].obj.setPos(-100, -100, -100)
                self.pieces[dest] = None

        def move_(start, dest):
            if self.pieces[start] is None:
                raise ValueError
            self.pieces[dest] = self.pieces[start]
            self.pieces[dest].obj.setPos(TutChessboard.SquarePos(dest))
            if start != dest:
                self.pieces[start] = None

        if special == "x" and self.pieces[dest] is None:
            special = "ep"

        if special is None:
            move_(start, dest)

        elif special == "x":
            remove_(dest)
            move_(start, dest)

        elif special == "O-O":
            if self.turn == "White":
                move_(4, 6)
                move_(7, 5)

            else:
                move_(60, 62)
                move_(63, 61)

        elif special == "O-O-O":
            if self.turn == "White":
                move_(4, 2)
                move_(0, 3)

            else:
                move_(60, 58)
                move_(56, 59)

        elif special == "ep":
            if self.turn == "White":
                remove_(dest - 8)

            else:
                remove_(dest + 8)

            move_(start, dest)

        elif special in ("Q", "R", "B", "N"):
            remove_(start)
            remove_(dest)

            piecemap = {
                "Q": TutChessboard.Queen,
                "R": TutChessboard.Rook,
                "B": TutChessboard.Bishop,
                "N": TutChessboard.Knight,
            }
            color = TutChessboard.PIECEBLACK
            if self.turn == "White":
                color = TutChessboard.WHITE

            self.pieces[dest] = piecemap[special](dest, color)

        else:
            print(start, dest, special)
            raise Exception

        if self.turn == "White":
            self.turn = "Black"

        else:
            self.turn = "White"


class mychessboard(pandachessboard):

    def __init__(self, boardparent):
        self.boardparent = boardparent
        pandachessboard.__init__(self)

    def move(self, move):
        self.boardparent.move(move)


class chessboard(object):

    def __init__(self, player="Both"):
        assert player in ("White", "Black", "Both", None)
        self.player = player
        self.moveprocessors = []
        self.board = mychessboard(self)

    def make_move(self, move):
        self.board.make_move(move)

    def trig_make_move(self):  # TODO: remove
        self.make_move(self.prop_move)  # TODO: remove

    def add_moveprocessor(self, moveprocessor):
        self.moveprocessors.append(moveprocessor)

    def set_turn(self, turn_func):
        self.turn = turn_func

    def move(self, move):
        if self.player != "Both":
            if self.turn() != self.player or self.player is None:
                raise ValueError

        for f in self.moveprocessors:
            f(move)

        # self.eventhandler_lock()
        # try:
        #  for f in self.moveprocessors: f(move)
        # finally:
        #  self.eventhandler_unlock()
    """
  def place(self):
    p = plugin_supplier(self.make_move) 
    libcontext.plugin(("game","make_move"),p)

    s = socket_single_required(self.set_turn)
    libcontext.socket(("game","turn"), s)
  
    s = socket_container(self.add_moveprocessor)
    libcontext.socket(("game","process_move"), s)
    
    libcontext.socket(("eventhandler","lock"), 
      socket_single_required(self.set_eventhandler_lock))
    
    libcontext.socket(("eventhandler","unlock"), 
      socket_single_required(self.set_eventhandler_unlock))
   """
import hive as h


def build_chessboard(cls, i, ex, args):
    prop_move = h.property(cls, "prop_move", "str")  # TODO: make buffer
    i.make_move = h.push_in(prop_move)
    i.trig_make_move = h.triggerable(cls.trig_make_move)  # TODO: make modifier
    h.trigger(i.make_move, i.trig_make_move)

    ex.make_move = h.antenna(i.make_move)
    ex.do_make_move = cls.make_move
    ex.p_make_move = h.plugin(cls.make_move)
    ex.prop_move = prop_move
    ex.set_turn = h.socket(cls.set_turn)
    ex.add_moveprocessor = h.socket(cls.add_moveprocessor)

chessboard = h.hive("chessboard", build_chessboard, chessboard)

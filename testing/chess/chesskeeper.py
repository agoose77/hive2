from copy import copy, deepcopy


def parse_move(m, turn, piecenames=("K", "Q", "R", "N", "B")):
    if m == "0-0":
        m = "O-O"
    if m == "0-0-0":
        m = "O-O-O"
    if len(m) == 0:
        raise ValueError
    if m[0] == piecenames[0]:
        if m[1:] == "e8-g8":
            m = "O-O"
        elif m[1:] == "e1-g1":
            m = "O-O"
        elif m[1:] == "e8-c8":
            m = "O-O-O"
        elif m[1:] == "e1-c1":
            m = "O-O-O"

    letters = ("a", "b", "c", "d", "e", "f", "g", "h")
    if m == "O-O":
        if turn == "White":
            return ((4, 0), (7, 0), m)
        return ((4, 7), (7, 7), m)
    elif m == "O-O-O":
        if turn == "White":
            return ((4, 0), (0, 0), m)
        return ((4, 7), (0, 7), m)
    px = m.find("-")
    if px == -1:
        px = m.index("x")
    if px == 3:
        piece = m[0]
        m = m[1:]
    else:
        piece = "p"
    start = (letters.index(m[0]), int(m[1]) - 1)
    dest = (letters.index(m[3]), int(m[4]) - 1)
    special = None
    if m[2] == "x":
        special = "x"
    if piece == "p":
        mapping = ("K", "Q", "R", "N", "B")
        if len(m) > 5 and m[5] not in mapping and m[5].upper() in mapping:
            m = m[:5] + m[5].upper()
        if len(m) > 6 and m[2] == "x" and m[5:7] == "ep":
            special = "ep"
        elif turn == "White" and start[1] == 6:
            if len(m) > 5 and m[5] != "x":
                special = mapping[piecenames.index(m[5])]
        elif turn == "Black" and start[1] == 1:
            if len(m) > 5 and m[5] != "x":
                special = mapping[piecenames.index(m[5])]
    return start, dest, special


class chesskeeper(object):
    _piecenames = ("K", "Q", "R", "N", "B", "White", "Black")

    def __init__(self):
        self._grid_reset()

    def _grid_reset(self):
        self._grid = {}
        for x in range(8):
            for y in range(8):
                self._grid[(x, y)] = None

    def new(self):
        self._pastmoves = []
        self._legalmoves = []
        self.turn = "White"
        self.check = False
        self._grid_reset()
        self._castling = {
            "White": {"O-O": None, "O-O-O": None}, "Black": {"O-O": None, "O-O-O": None}}
        self._ep = None  # for en passant rule
        self.finished = False
        pieces = ("R", "N", "B", "Q", "K", "B", "N", "R")
        for color in "White", "Black":
            base, front = 0, 1
            if color == "Black":
                base, front = 7, 6
            for x in range(8):
                self._grid[(x, front)] = ("p", color)
            for x, piece in zip(range(8), pieces):
                self._grid[(x, base)] = (piece, color)
        self._legalmoves = self._calc_legal_moves()
        return self

    def _check_for_check(self):
        # evaluate if one of the legal moves targets the opponent king
        other = "Black"
        if self.turn == "Black":
            other = "White"
        for start, dest, special in self._legalmoves:
            if special in ("O-O", "O-O-O"):
                continue
            v = self._grid[dest]
            if v is None:
                continue
            if v == ("K", other):
                return True
        return False

    def _calc_moves_line(self, line):
        ret = []
        for xx, yy in line:
            v = self._grid[(xx, yy)]
            if v != None:
                if v[1] != self.turn:
                    ret.append((xx, yy))
                break
            ret.append((xx, yy))
        return ret

    def _calc_moves_diagonal(self, x, y):
        ret = []
        lines = [[], [], [], []]
        for n in range(1, 8):
            xmin, xmax = x - n, x + n
            ymin, ymax = y - n, y + n
            if xmax <= 7 and ymax <= 7:
                lines[0].append((xmax, ymax))
            if xmax <= 7 and ymin >= 0:
                lines[1].append((xmax, ymin))
            if xmin >= 0 and ymax <= 7:
                lines[2].append((xmin, ymax))
            if xmin >= 0 and ymin >= 0:
                lines[3].append((xmin, ymin))
        for line in lines:
            ret += self._calc_moves_line(line)
        return ret

    def _calc_moves_horizontal(self, x, y):
        ret = []
        lines = [[], [], [], []]
        for n in range(1, 8):
            xmin, xmax = x - n, x + n
            ymin, ymax = y - n, y + n
            if xmax <= 7:
                lines[0].append((xmax, y))
            if ymax <= 7:
                lines[1].append((x, ymax))
            if xmin >= 0:
                lines[2].append((xmin, y))
            if ymin >= 0:
                lines[3].append((x, ymin))
        for line in lines:
            ret += self._calc_moves_line(line)
        return ret

    def _valid_target(self, x, y):
        if x < 0 or x > 7:
            return False
        if y < 0 or y > 7:
            return False
        v = self._grid[(x, y)]
        if v is None:
            return True
        return v[1] != self.turn

    def _calc_moves_king(self, x, y):
        ret = []
        for dx in 1, 0, -1:
            for dy in 1, 0, -1:
                if dx == dy == 0:
                    continue
                xx, yy = x + dx, y + dy
                if self._valid_target(xx, yy):
                    ret.append((xx, yy))
        return ret

    def _calc_moves_knight(self, x, y):
        ret = []
        for d in ((2, 1), (1, 2)):
            dx, dy = d
            for xmin in 1, -1:
                for ymin in 1, -1:
                    xx, yy = x + xmin * dx, y + ymin * dy
                    if self._valid_target(xx, yy):
                        ret.append((xx, yy))
        return ret

    def _calc_moves_pawn(self, x, y):
        ret, special = [], []
        dy, ty = 1, y
        if self.turn == "Black":
            dy, ty = -1, 7 - y
        # forward
        if self._grid[(x, y + dy)] is None:
            if ty == 6:  # promote
                for piece in ("Q", "R", "B", "N"):
                    special.append(((x, y), (x, y + dy), piece))
            else:
                ret.append((x, y + dy))
            if ty == 1:  # two forward
                if self._grid[(x, y + 2 * dy)] is None:
                    ret.append((x, y + 2 * dy))

        # take
        for dx in (-1, 1):
            if x + dx < 0 or x + dx > 7:
                continue
            v = self._grid[(x + dx, y + dy)]
            if v is not None and v[1] != self.turn:
                if ty == 6:  # promote
                    for piece in ("Q", "R", "B", "N"):
                        special.append(((x, y), (x + dx, y + dy), piece))
                else:
                    ret.append((x + dx, y + dy))
            # take en passant
            if self._ep is not None and ty == 4:
                if self._ep == (x + dx, y):
                    special.append(((x, y), (x + dx, y + dy), "ep"))

        return ret, special

    def _calc_legal_castling(self):
        y = 0
        if self.turn == "Black":
            y = 7
        other = "Black"
        if self.turn == "Black":
            other = "White"

        #-king not in check
        if self.check:
            return []
        special = []
        for x, dx, code in (0, (1, 2, 3), "O-O-O"), (7, (6, 5), "O-O"):
            #-castling must be available
            if code not in self._castling[self.turn]:
                continue
            #-no pieces between king and rook
            empty = False
            for xx in dx:
                if self._grid[(xx, y)] != None:
                    break
            else:
                empty = True
            if not empty:
                continue
            #-king can move one square towards rook
            c = self.copy()
            m = ((4, y), (dx[-1], y), None)
            self._do_move(m)
            self.turn = other
            newmoves = self._calc_all_moves()
            self._legalmoves = newmoves

            check = self._check_for_check()
            self.restore_copy(c)
            if check:
                continue
            # all conditions met
            special.append(((4, y), (x, y), code))
        return special

    def _calc_all_moves(self):
        ret = self._calc_legal_castling()
        for x in range(8):
            for y in range(8):
                v = self._grid[(x, y)]
                if v is None:
                    continue
                piece, color = v
                if color != self.turn:
                    continue
                if piece == "K":
                    moves = self._calc_moves_king(x, y)
                elif piece == "Q":
                    moves = self._calc_moves_diagonal(x, y)
                    moves += self._calc_moves_horizontal(x, y)
                elif piece == "R":
                    moves = self._calc_moves_horizontal(x, y)
                elif piece == "B":
                    moves = self._calc_moves_diagonal(x, y)
                elif piece == "N":
                    moves = self._calc_moves_knight(x, y)
                elif piece == "p":
                    moves, special = self._calc_moves_pawn(x, y)
                    ret += special
                ret += [((x, y), m, None) for m in moves]
        return ret

    def _calc_legal_moves(self):
        moves = self._calc_all_moves()
        # eliminate moves that would bring or leave own king in check
        c = self.copy()
        other = "Black"
        if self.turn == "Black":
            other = "White"
        ret = []
        for m in moves:
            mstr = self._format_move(m)
            self._do_move(m)
            self.turn = other
            newmoves = self._calc_all_moves()
            self._legalmoves = newmoves
            if not self._check_for_check():
                ret.append(m)
            self.restore_copy(c)
        return ret

    def _format_move(self, move):
        letters = ("a", "b", "c", "d", "e", "f", "g", "h")
        start, dest, special = move
        if special in ("O-O", "O-O-O"):
            return special
        if special is None:
            special = ""
        c = "-"
        if start not in self._grid or dest not in self._grid:
            raise ValueError
        if self._grid[dest] != None or special == "ep":
            c = "x"
        if self._grid[start] is None:
            raise ValueError
        p = self._grid[start][0]
        if p == "p":
            p = ""
        else:
            mapping = {"K": 0, "Q": 1, "R": 2, "N": 3, "B": 4}
            if p not in mapping and p.toupper() in mapping:
                p = p.toupper()
            p = self._piecenames[mapping[p]]
        if special == "x":
            special = ""
        return "%s%s%d%s%s%d%s" % (p, letters[start[0]], start[1] + 1, c,
                                   letters[dest[0]], dest[1] + 1, special)

    def format_move(self, move):
        parsedmove = parse_move(move, self.turn)
        return self._format_move(parsedmove)

    def _do_move(self, move):
        start, dest, special = move
        if special == "x":
            special = None
        grid = self._grid
        p = grid[start][0]
        if p == "K":
            self._castling[self.turn] = {}
        elif p == "R":
            if start == (0, 0):
                self._castling["White"].pop("O-O-O", None)
            elif start == (7, 0):
                self._castling["White"].pop("O-O", None)
            elif start == (0, 7):
                self._castling["Black"].pop("O-O-O", None)
            elif start == (7, 7):
                self._castling["Black"].pop("O-O", None)
        if special is None:
            grid[dest] = grid[start]
            grid[start] = None
            self._ep = None
            if grid[dest][0] == "p" and abs(dest[1] - start[1]) == 2:
                self._ep = dest
        elif special == "ep":
            grid[dest] = grid[start]
            grid[start] = None
            grid[self._ep] = None
            self._ep = None
        elif special in ("O-O", "O-O-O"):
            king, rook = start, dest
            dx = (rook[0] - king[0])
            dx /= abs(dx)
            grid[(king[0] + 2 * dx, king[1])] = grid[king]
            grid[king] = None
            grid[(king[0] + dx, king[1])] = grid[rook]
            grid[rook] = None
            self._ep = None
        else:  # promotion
            grid[dest] = (special, grid[start][1])
            grid[start] = None
        self._pastmoves.append(move)

    def _make_move(self, move):
        # check if move in legal moves; if not, illegal
        move0 = move
        if move[2] == "x":
            move = (move[0], move[1], None)
        if move not in self._legalmoves and move[2] is None:
            move = (move[0], move[1], "ep")
        if move not in self._legalmoves:
            raise ValueError(move0)
        # do move
        self._do_move(move)
        # re-calculate legal moves for the same player
        self._legalmoves = self._calc_legal_moves()
        # check if one of the new legal moves is to capture king; if so, check
        self.check = self._check_for_check()
        if self.turn == "White":
            self.turn = "Black"
        else:
            self.turn = "White"
        # re-calculate legal moves for the new player
        self._legalmoves = self._calc_legal_moves()
        # check if no legal moves; if so, checkmate or draw
        if len(self._legalmoves) == 0:
            self.finished = True

    def make_move(self, move):
        m = parse_move(move, self.turn, self._piecenames)
        try:
            self._make_move(m)
        except ValueError:
            raise ValueError(move)

    def copy(self):
        ret = chesskeeper()
        ret._grid = copy(self._grid)
        ret._piecenames = deepcopy(self._piecenames)
        ret._pastmoves = copy(self._pastmoves)
        ret._legalmoves = copy(self._legalmoves)
        ret.turn = self.turn
        ret.check = self.check
        ret._castling = deepcopy(self._castling)
        ret._ep = self._ep
        ret.finished = self.finished
        return ret

    def restore_copy(self, chesskeepercopy):
        c = chesskeepercopy.copy()
        self._grid = c._grid
        self._piecenames = c._piecenames
        self._pastmoves = c._pastmoves
        self._legalmoves = c._legalmoves
        self.turn = c.turn
        self.check = c.check
        self._castling = c._castling
        self._ep = c._ep
        self.finished = c.finished

    def trig_make_move(self):  # TODO: remove
        self.make_move(self.prop_move)  # TODO: remove
"""      
from bee import *
import libcontext
from libcontext.pluginclasses import *
from libcontext.socketclasses import *

from .. import chesskeeper as comp_chesskeeper


class chesskeeper(drone):
  def __init__(self):
    self.keeper = comp_chesskeeper.chesskeeper().new()
  def place(self):
    p = plugin_supplier(lambda: getattr(self.keeper, "finished")) 
    libcontext.plugin(("game", "finished"),p)
    
    p = plugin_supplier(self.keeper.format_move) 
    libcontext.plugin(("game", "format_move"),p)
    
    p = plugin_supplier(self.keeper.make_move) 
    libcontext.plugin(("game", "make_move"),p)
"""

import hive as h


def build_chesskeeper(cls, i, ex, args):
    ex.finished = h.property(cls, "finished", "bool")
    ex.make_move = cls.make_move
    ex.format_move = cls.make_move

    prop_move = h.property(cls, "prop_move", "str")  # TODO: make buffer
    i.make_move = h.push_in(prop_move)
    i.trig_make_move = h.triggerable(cls.trig_make_move)  # TODO: make modifier
    h.trigger(i.make_move, i.trig_make_move)

    ex.make_move = h.antenna(i.make_move)
    ex.do_make_move = cls.make_move
    ex.p_make_move = h.plugin(cls.make_move)
    ex.prop_move = prop_move
    ex.p_format_move = h.plugin(cls.format_move)

chessboard = h.hive("chessboard", build_chesskeeper, chesskeeper)

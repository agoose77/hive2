
import weakref
from PySide import QtCore, QtGui

from .socket import Socket
from math import *
from operator import sub


def cartesian_to_polar(x, y):
    r = sqrt(x * x + y * y)
    theta = atan2(y, x)
    return r, theta


def polar_to_cartesian(r, theta):
    return r * cos(theta), r * sin(theta)


def average_polar(p1, p2):
    r1, theta1 = p1
    r2, theta2 = p2
    thmin, thmax = theta1, theta2
    if thmin > thmax:
        thmin, thmax = thmax, thmin
    thdif1 = thmax - thmin
    thdif2 = thmin - thmax + 2 * pi
    if thdif1 < thdif2:
        theta = thmin + 0.5 * thdif1
    else:
        theta = thmax + 0.5 * thdif2
        if theta > pi: theta -= 2 * pi
    r = (r1 + r2) / 2.0
    return r, theta


def interpolate_tangents(t1, t2):
    p1 = cartesian_to_polar(t1.x(), t1.y())
    p2 = cartesian_to_polar(t2.x(), t2.y())
    r, theta = average_polar(p1, p2)
    r = 0.5 * r
    r = min(r, 100)
    x, y = polar_to_cartesian(r, theta)
    return QtCore.QPointF(x, y)


class Connection(QtGui.QGraphicsItem):
    _start_socket = None
    _end_socket = None

    def __init__(self, start_socket, end_socket=None, id_=None):
        QtGui.QGraphicsItem.__init__(self, None, start_socket.scene())

        if id_ is None:
            id_ = id(self)
        self.id = id_

        self._rect = QtCore.QRectF(0, 0, 0, 0)

        self._color = start_socket.colorRef()
        self._pen = QtGui.QPen(self._color)
        self._is_temp_connection = False
        self._path = QtGui.QPainterPath()
        self._key_points = []

        self.set_start_socket(start_socket)

        if end_socket is None:
            # creating a dummy endHook for temporary connection dragging, 
            #  the "input" and shape/style parameters have no effect
            end_mode = "output" if start_socket.is_input else "input"
            end_socket = Socket(start_socket.parent_socket_row, end_mode, start_socket._shape, self._active_style, parent_item=self)
            end_socket.boundingRect().setSize(QtCore.QSizeF(2.0, 2.0))
            self._is_temp_connection = True

        self.set_end_socket(end_socket)
        self.update_start_pos()

        self.setZValue(-1.0)
        self.set_active(False)

    @property
    def start_socket(self):
        if self._start_socket is None:
            return None

        return self._start_socket()

    @property
    def end_socket(self):
        if self._end_socket is None:
            return None

        return self._end_socket()

    def boundingRect(self):
        return self._rect

    def set_key_points(self, interpoints):
        s = self.scenePos()
        sx, sy = s.x(), s.y()
        self._key_points = [QtCore.QPointF(x - sx, -y - sy) for x, y in interpoints]

    def insert_key_point(self, index, coordinate):
        if index is None:
            self._key_points.append(coordinate)
        else:
            self._key_points.insert(index, coordinate)

    def remove_key_point(self, index):
        self._key_points.pop(self._key_points)

    def find_nearest_key_points(self, coordinate):
        points = []

        start_socket = self._start_socket()
        start_pos = start_socket.scenePos() + start_socket.boundingRect().center()
        points.append(start_pos)

        points += self._key_points
        distances = [(i, sub(point, coordinate)) for i, point in enumerate(points)]

        if self.end_socket:
            end_socket = self.end_socket
            end_position = end_socket.scenePos() + end_socket.boundingRect().center()
            distances.append((-1, self._difDistance(end_position, coordinate)))

        if len(distances) == 1:
            return distances[0][0], None

        distances.sort(key=lambda item: item[1])
        return distances[0][0], distances[1][0]

    def set_active(self, active):
        assert active in (True, False), active

        if active:
            self._pen.setWidth(3)
        else:
            self._pen.setWidth(2)

        value = self._active_style

        if value == "dashed":
            self._pen.setStyle(QtCore.Qt.DashLine)

        elif value == "solid":
            self._pen.setStyle(QtCore.Qt.SolidLine)

        elif value == "dot":
            self._pen.setStyle(QtCore.Qt.DotLine)

        else:
            raise ValueError("Unknown pen style '%s'" % value)

    def set_selected(self, selected):
        assert selected in (True, False), selected

        self.set_active(selected)
        if selected:
            self._pen.setWidth(5)

    def on_deleted(self):
        if self.scene():
            self.scene().removeItem(self)

        self.set_end_socket(None)
        self.set_start_socket(None)

    def update_start_pos(self):
        start_socket = self.start_socket
        self.setPos(start_socket.scenePos() + start_socket.boundingRect().center())

        self.update_path()

    def update_end_pos(self):
        self.update_path()

    def update_visibility(self):
        visible = self.start_socket.isVisible() and self.end_socket.isVisible()
        self.setVisible(visible)

    def set_color(self, color):
        if isinstance(color, tuple):
            color = QtGui.QColor(*color)

        else:
            color = QtGui.QColor(color)

        self._color = color

    def set_start_socket(self, socket):
        if self.start_socket:
            self.start_socket.remove_connection(self)

        self._start_socket = None
        self._active_style = "dot"

        if socket is not None:
            self._start_socket = weakref.ref(socket)
            socket.add_connection(self)
            self._active_style = socket._style

    def set_end_socket(self, socket):
        if self.end_socket:
            self.end_socket.remove_connection(self)

        self._end_socket = None

        if socket is not None:
            self._end_socket = weakref.ref(socket)
            socket.add_connection(self)

    def find_closest_socket(self):
        closest_socket = None

        colliding_items = self.end_socket.collidingItems(QtCore.Qt.IntersectsItemBoundingRect)

        for colliding_item in colliding_items:
            if isinstance(colliding_item, Socket):
                if colliding_item.is_input and colliding_item.isVisible():
                    closest_socket = colliding_item

                break

        return closest_socket

    def update_path(self):
        end_hook = self.end_socket

        if end_hook is None:
            return

        self.prepareGeometryChange()
        end_pos = self.mapFromItem(end_hook, 0.0, 0.0) + end_hook.boundingRect().center()

        if not self._key_points:
            tangent_length = (abs(end_pos.x()) / 2.0) + (abs(end_pos.y()) / 4.0)
            tangent_length2 = tangent_length

        else:
            first_pos = self._key_points[0]
            tangent_length = (abs(first_pos.x()) / 2.0) + (abs(first_pos.y()) / 4.0)
            last_pos = self._key_points[-1]
            last_segment = end_pos - last_pos
            tangent_length2 = (abs(last_segment.x()) / 2.0) + (abs(last_segment.y()) / 4.0)

        spread = 60.0 / 180.0 * pi

        # Find connection index
        index, number_connections = self.start_socket.get_index_info(self)

        dev = (index - number_connections / 2.0 + 0.5) * min(spread, pi / (number_connections + 2))
        tx = tangent_length * cos(dev)
        ty = tangent_length * sin(dev)
        start_tangent = QtCore.QPointF(tx, ty)

        end_tangent = QtCore.QPointF(end_pos.x() - tangent_length2, end_pos.y())

        path = QtGui.QPainterPath()
        current_tangent = start_tangent
        current_pos = QtCore.QPointF(0.0, 0.0)

        for i, point in enumerate(self._key_points):
            if i == len(self._key_points) - 1:
                next_position = end_pos

            else:
                next_position = self._key_points[i + 1]

            next_tangent = interpolate_tangents((point - current_pos), (next_position - point))
            path.cubicTo(current_tangent, point - next_tangent, point)

            current_tangent = point + next_tangent
            current_pos = point

        path.cubicTo(current_tangent, end_tangent, end_pos)

        stroke_width = self._pen.widthF()
        rect = path.boundingRect().adjusted(-stroke_width, -stroke_width, stroke_width, stroke_width)

        self._path = path
        self._rect = rect

    def paint(self, painter, option, widget):
        self._pen.setColor(self._color)
        painter.setPen(self._pen)
        painter.drawPath(self._path)
import weakref
from math import *
from operator import sub

from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF, QSizeF, QTimer
from PyQt5.QtGui import QPainterPath, QVector2D, QPen, QColor

from .socket import QtSocket


from collections import namedtuple


Polar = namedtuple('Polar', 'r theta')


def cartesian_to_polar(x, y):
    r = sqrt(x * x + y * y)
    theta = atan2(y, x)
    return Polar(r, theta)


def polar_to_cartesian(p):
    return p.r * cos(p.theta), p.r * sin(p.theta)


def average_polar(p1, p2):
    r_1, theta_1 = p1
    r_2, theta_2 = p2

    theta = ((theta_1 + theta_2)/2) % (2*pi)

    # Sign between - pi and + pi
    if theta > pi:
        theta -= 2 * pi

    r = (r_1 + r_2) / 2.0
    return r, theta


def interpolate_tangents(t1, t2):
    p1 = cartesian_to_polar(t1.x(), t1.y())
    p2 = cartesian_to_polar(t2.x(), t2.y())
    r, theta = average_polar(p1, p2)
    r = min(0.5 * r, 100)
    x, y = polar_to_cartesian(r, theta)
    return QPointF(x, y)


class Connection(QGraphicsItem):
    _startSocket = None
    _endSocket = None

    def __init__(self, start_socket, end_socket=None, id_=None, style="solid", curve=True):
        QGraphicsItem.__init__(self, None)

        if id_ is None:
            id_ = id(self)

        self.id = id_

        self._rect = QRectF(0, 0, 0, 0)

        self._isTempConnection = False

        self._path = QPainterPath()

        self._activeStyle = style
        self._curve = curve
        self._isActive = False

        self._color = start_socket.colorRef()
        self._pen = QPen(self._color)

        self._penWidthInactive = 2
        self._penWidthActive = 4
        self._penWidthBlink = 8

        self._penWidth = self._penWidthInactive

        self.setStartSocket(start_socket)

        self._keyPoints = []

        self._centerWidget = None

        if end_socket is None:
            # creating a dummy endHook for temporary connection dragging, 
            #  the "input" and shape/style parameters have no effect
            end_mode = "output" if start_socket.isInput() else "input"
            end_socket = QtSocket(start_socket.parentSocketRow(), end_mode, start_socket._shape, parent_item=self)
            end_socket.boundingRect().setSize(QSizeF(2.0, 2.0))
            self._isTempConnection = True

        self.setEndConnection(end_socket)

        self.updateStartPos()

        self.setZValue(-1.0)
        self.setActiveState(False)

        self._blink_depth = 0

    def startSocket(self):
        if self._startSocket is None:
            return None

        return self._startSocket()

    def endSocket(self):
        if self._endSocket is None:
            return None

        return self._endSocket()

    @property
    def index(self):
        index, total = self.startSocket().getIndexInfo(self)
        return index

    @property
    def is_active(self):
        return self._isActive

    def boundingRect(self):
        return self._rect

    def setKeyPoints(self, interpoints):
        s = self.scenePos()
        sx, sy = s.x(), s.y()
        self._keyPoints = [QPointF(x - sx, -y - sy) for x, y in interpoints]

    def insertKeyPoint(self, index, coordinate):
        if index is None:
            self._keyPoints.append(coordinate)
        else:
            self._keyPoints.insert(index, coordinate)

    def removeKeyPoint(self, index):
        self._keyPoints.pop(self._keyPoints)

    def findNearestKeyPoints(self, coordinate):
        points = []

        start_socket = self._startSocket()
        start_pos = start_socket.scenePos() + start_socket.boundingRect().center()
        points.append(start_pos)

        points += self._keyPoints
        distances = [(i, sub(point, coordinate)) for i, point in enumerate(points)]

        if self.endSocket():
            end_socket = self.endSocket()
            end_position = end_socket.scenePos() + end_socket.boundingRect().center()
            distances.append((-1, self._difDistance(end_position, coordinate)))

        if len(distances) == 1:
            return distances[0][0], None

        distances.sort(key=lambda item: item[1])
        return distances[0][0], distances[1][0]

    def intersectsCircle(self, position, rect, size):
        size_sqr = size ** 2
        scene_translation = self.startSocket().sceneTransform()
        connection_rect = scene_translation.mapRect(self._rect)

        # Line circle intersection test http://i.stack.imgur.com/P556i.png
        if connection_rect.contains(rect) or (connection_rect.width() <= size or connection_rect.height() <= size):
            connection_path = scene_translation.map(self._path)
            simplified_path = connection_path.simplified()

            element_count = simplified_path.elementCount() - 1

            # In case path is linear
            if element_count == -1:
                simplified_path = connection_path
                element_count = simplified_path.elementCount()

            previous_point = None
            for i in range(element_count):
                element = simplified_path.elementAt(i)
                point = QPointF(element.x, element.y)

                previous_point, _previous_point = point, previous_point

                if _previous_point is None:
                    continue

                to_position = QVector2D(position - _previous_point)
                to_end = QVector2D(point - _previous_point)

                to_end_length = to_end.length()
                if not to_end_length:
                    continue

                projection = QVector2D.dotProduct(to_position, to_end) / to_end_length

                # Projected point lies within this segment
                if 0 <= projection <= to_end_length:
                    dist_path_sqr = to_position.lengthSquared() - projection ** 2

                    if dist_path_sqr < size_sqr:
                        return self

    def intersectsLine(self, line, path_rect):
        scene_translation = self.startSocket().sceneTransform()
        connection_rect = scene_translation.mapRect(self._rect)

        if connection_rect.contains(path_rect) or path_rect.contains(connection_rect) \
                or path_rect.intersects(connection_rect):

            connection_path = scene_translation.map(self._path)
            simplified_path = connection_path.simplified()

            element_count = simplified_path.elementCount() - 1

            # In case path is linear
            if element_count == -1:
                simplified_path = connection_path
                element_count = simplified_path.elementCount()

            previous_point = None
            for i in range(element_count):
                element = simplified_path.elementAt(i)

                point = QPointF(element.x, element.y)
                if previous_point is not None:
                    segment = QLineF(previous_point, point)

                    intersect_point = QPointF()
                    intersect_type = segment.intersect(line, intersect_point)

                    if intersect_type == QLineF.BoundedIntersection:
                        return True

                previous_point = point

    def blink(self, time):
        self._pen.setWidth(self._penWidthBlink)
        self.update()

        timer = QTimer()

        def on_finished():
            self._blink_depth -= 1

            # Allow multiple blinks without flashing
            if not self._blink_depth:
                self._pen.setWidth(self._penWidth)
                self.update()

        self._blink_depth += 1
        timer.singleShot(1000 * time, on_finished)

    def setActiveState(self, active):
        assert active in (True, False), active

        if active:
            self._penWidth = self._penWidthActive

        else:
            self._penWidth = self._penWidthInactive

        self._pen.setWidth(self._penWidth)

        value = self._activeStyle

        if value == "dashed":
            self._pen.setStyle(Qt.DashLine)

        elif value == "solid":
            self._pen.setStyle(Qt.SolidLine)

        elif value == "dot":
            self._pen.setStyle(Qt.DotLine)

        else:
            raise ValueError("Unknown pen style '%s'" % value)

        self._isActive = active
        self.update()

    def onDeleted(self):
        self.setEndConnection(None)
        self.setStartSocket(None)

    def updateStartPos(self):
        start_socket = self.startSocket()
        self.setPos(start_socket.scenePos() + start_socket.boundingRect().center())

        self.updatePath()

    def updateEndPos(self):
        self.updatePath()

    def updateVisibility(self):
        visible = self.startSocket().isVisible() and self.endSocket().isVisible()
        self.setVisible(visible)

    def setColor(self, color):
        if isinstance(color, tuple):
            color = QColor(*color)

        else:
            color = QColor(color)

        self._color = color

    def setStartSocket(self, socket):
        if self.startSocket():
            self.startSocket().removeConnection(self)

        self._startSocket = None

        if socket is not None:
            self._startSocket = weakref.ref(socket)
            socket.addConnection(self)

    def setEndConnection(self, socket):
        if self.endSocket():
            self.endSocket().removeConnection(self)

        self._endSocket = None

        if socket is not None:
            self._endSocket = weakref.ref(socket)
            socket.addConnection(self)

    def setCenterWidget(self, widget):
        self._centerWidget = widget

    def centerWidget(self):
        return self._centerWidget

    def findClosestSocket(self):
        closest_socket = None

        colliding_items = self.endSocket().collidingItems(Qt.IntersectsItemBoundingRect)

        for colliding_item in colliding_items:
            if isinstance(colliding_item, QtSocket):
                if colliding_item.isInput() and colliding_item.isVisible():
                    closest_socket = colliding_item

                break

        return closest_socket

    def updatePath(self):
        end_hook = self.endSocket()

        if end_hook is None:
            return

        self.prepareGeometryChange()
        end_pos = self.mapFromItem(end_hook, 0.0, 0.0) + end_hook.boundingRect().center()

        if self._curve:
            if not self._keyPoints:
                tangent_length = (abs(end_pos.x()) / 2.0) + (abs(end_pos.y()) / 4.0)
                tangent_length2 = tangent_length

            else:
                first_pos = self._keyPoints[0]
                tangent_length = (abs(first_pos.x()) / 2.0) + (abs(first_pos.y()) / 4.0)
                last_pos = self._keyPoints[-1]
                last_segment = end_pos - last_pos
                tangent_length2 = (abs(last_segment.x()) / 2.0) + (abs(last_segment.y()) / 4.0)

            spread = 60.0 / 180.0 * pi

            # Find connection index
            index, number_connections = self.startSocket().getIndexInfo(self)

            dev = (index - number_connections / 2.0 + 0.5) * min(spread, pi / (number_connections + 2))
            tx = tangent_length * cos(dev)
            ty = tangent_length * sin(dev)

            start_tangent = QPointF(tx, ty)
            end_tangent = QPointF(end_pos.x() - tangent_length2, end_pos.y())

            path = QPainterPath()
            path.cubicTo(start_tangent, end_tangent, end_pos)

        # Dot styles are used for relationships
        else:
            path = QPainterPath()
            path.lineTo(end_pos)

        stroke_width = self._pen.widthF()
        rect = path.boundingRect().adjusted(-stroke_width, -stroke_width, stroke_width, stroke_width)

        # draw widget
        center_widget = self._centerWidget

        if center_widget is not None:
            center = path.pointAtPercent(0.5)
            center_widget.onUpdated(center, text=str(self.index))

        self._path = path
        self._rect = rect

    def onSocketHoverEnter(self):
        center_widget = self._centerWidget

        if center_widget is not None:
            center_widget.setVisible(True)

    def onSocketHoverExit(self):
        center_widget = self._centerWidget
        if center_widget is not None:
            center_widget.setVisible(False)

    def paint(self, painter, option, widget):
        self._pen.setColor(self._color)
        painter.setPen(self._pen)
        painter.drawPath(self._path)

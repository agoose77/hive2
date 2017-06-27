from collections import OrderedDict
from sys import float_info

from PyQt5.QtWidgets import QSpinBox, QLineEdit, QDoubleSpinBox, QWidget, QHBoxLayout, QCheckBox, QComboBox, QToolButton
from PyQt5.QtGui import QColor, QIcon, QPixmap

from hive import data_types_match, MatchFlags
from .colour_button import ColorButton
from .code_editor import CodeEditor
from .key_selector import QKeySelector
from ..observer import Observable


MAX_INT = 2 ** 16 - 1
MAX_FLOAT = float_info.max

INT_RANGE = -MAX_INT, MAX_INT
FLOAT_RANGE = -MAX_FLOAT, MAX_FLOAT
FLOAT_STEP = 0.1


class WidgetController:

    on_changed = Observable()

    def __init__(self, getter, setter):
        self.setter = setter
        self.getter = getter

    def _on_changed(self):
        self.on_changed(self.getter())

    @property
    def value(self):
        return self.getter()

    @value.setter
    def value(self, value):
        try:
            self.setter(value)

        except Exception as err:
            print("Unable to set value {}: {}".format(value, err))


def _create_str():
    widget = QLineEdit()

    getter = widget.text
    setter = lambda value: widget.setText(value)

    controller = WidgetController(getter, setter)

    def on_changed(value=None):
        controller._on_changed()

    widget.textChanged.connect(on_changed)
    controller.__on_changed = on_changed

    return widget, controller


def _create_key():
    widget = QKeySelector()

    getter = widget.keycode
    setter = lambda value: widget.setKeycode(value)

    controller = WidgetController(getter, setter)

    def on_changed(value=None):
        controller._on_changed()

    widget.keySelected.connect(on_changed)
    controller.__on_changed = on_changed

    return widget, controller


def _create_code():
    widget = CodeEditor()

    getter = widget.toPlainText
    setter = lambda value: widget.setPlainText(value)

    controller = WidgetController(getter, setter)

    def on_changed():
        controller._on_changed()

    widget.textChanged.connect(on_changed)
    controller.__on_changed = on_changed

    return widget, controller


def _create_int():
    widget = QSpinBox()

    widget.setRange(*INT_RANGE)

    getter = widget.value
    setter = lambda value: widget.setValue(value)

    controller = WidgetController(getter, setter)
    widget.valueChanged.connect(lambda value: controller._on_changed())

    return widget, controller


def _create_float():
    widget = QDoubleSpinBox()

    widget.setRange(*FLOAT_RANGE)
    widget.setSingleStep(FLOAT_STEP)

    getter = widget.value
    setter = lambda value: widget.setValue(value)

    controller = WidgetController(getter, setter)
    widget.valueChanged.connect(lambda value: controller._on_changed())

    return widget, controller


def _create_bool():
    widget = QCheckBox()

    getter = lambda: bool(widget.isChecked())
    setter = lambda value: widget.setChecked(value)

    controller = WidgetController(getter, setter)

    def on_changed(value=None):
        controller._on_changed()

    widget.stateChanged.connect(on_changed)
    controller.__on_changed = on_changed

    return widget, controller


def _create_vector():
    widget = QWidget()

    layout = QHBoxLayout()
    widget.setLayout(layout)

    # When an individual field is modified
    def field_changed(field_value):
        controller._on_changed()

    for i in range(3):
        field = QDoubleSpinBox()

        field.setRange(*FLOAT_RANGE)
        field.setSingleStep(FLOAT_STEP)
        field.valueChanged.connect(field_changed)

        layout.addWidget(field)

    def setter(value):
        for i, field_value in enumerate(value):
            field = layout.itemAt(i).widget()
            field.setValue(field_value)

    def getter():
        return tuple(layout.itemAt(i).widget().value() for i in range(3))

    controller = WidgetController(getter, setter)

    return widget, controller


def _create_euler():
    return _create_vector()


def _create_colour():
    """Create a colour widget to display a restricted set of options

    :param options: permitted option values
    """
    widget = ColorButton()

    layout = QHBoxLayout()
    layout.setSpacing(0.0)

    widget.setLayout(layout)

    def setter(colour_rgb):
        colour = QColor.fromRgb(*colour_rgb)
        widget.setColor(colour)

    def getter():
        return tuple(widget.color().getRgb())

    controller = WidgetController(getter, setter)

    def on_changed():
        controller._on_changed()

    widget.colorChanged.connect(on_changed)

    return widget, controller


def _create_repr():
    """Create a UI widget to edit a repr-able value"""
    widget = QLineEdit()

    getter = lambda: eval(widget.text())
    setter = lambda value: widget.setText(repr(value))

    controller = WidgetController(getter, setter)

    def text_changed(text):
        controller._on_changed()

    widget.textChanged.connect(text_changed)

    controller.value = None
    return widget, controller


def _create_options(options):
    """Create a UI combo widget to display a restricted set of options

    :param options: permitted option values
    """
    widget = QComboBox()

    for i, option in enumerate(options):
        widget.insertItem(i, str(option), option)

    getter = lambda: widget.itemData(widget.currentIndex())
    setter = lambda value: widget.setCurrentIndex(widget.findData(value))

    controller = WidgetController(getter, setter)
    widget.activated.connect(lambda value: controller._on_changed())
    return widget, controller


def _create_tuple():
    widget = QWidget()
    layout = QHBoxLayout()
    widget.setLayout(layout)

    button = QToolButton(widget)
    icon = QIcon()
    icon.addPixmap(QPixmap(":/images/icons/ellipsis.png"))
    button.setIcon(icon)
  #  button.setText("...")
    button.show()

    layout.addWidget(button)

    controller = WidgetController(lambda: (), lambda x: None)
    return widget, controller


_factories = OrderedDict((
    ('str.code', _create_code),
    ('str.keycode', _create_key),
    ('str', _create_str),
    ('int', _create_int),
    ('float', _create_float),
    ('bool', _create_bool),
    ('vector', _create_vector),
    ('euler', _create_euler),
    ('colour', _create_colour),
    ))


def create_widget(data_type="", options=None):
    """Create a UI widget to edit a specific value

    :param data_type: data type of value
    :param options: restrict values to a fixed option set
    """
    if options is not None:
        return _create_options(options)

    for factory_type, factory in _factories.items():
        print(factory_type, data_type)
        if data_types_match(factory_type, data_type, MatchFlags.match_source):
            print("MATCH")
            return factory()

    return _create_repr()

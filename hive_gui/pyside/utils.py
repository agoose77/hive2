from PySide.QtGui import *
from PySide.QtCore import *


class WidgetController:

    def __init__(self, getter, setter):
        self.on_changed = None
        self.setter = setter
        self.getter = getter

    def _on_changed(self, value):

        if callable(self.on_changed):
            self.on_changed(value)

    @property
    def value(self):
        return self.getter()

    @value.setter
    def value(self, value):
        try:
            self.setter(value)
        except Exception as err:
            print("Unable to set value {}: {}".format(value, err))


def create_widget(type_name=None, options=None, use_text_area=False):
    if options is not None:
        widget = QComboBox()
        for i, option in enumerate(options):
            widget.insertItem(i, str(option), option)

        getter = lambda: widget.itemData(widget.currentIndex())
        setter = lambda value: widget.setCurrentIndex(widget.findData(value))

        controller = WidgetController(getter, setter)
        widget.activated.connect(controller._on_changed)

    else:
        if type_name == "str":
            if use_text_area:
                widget = QTextEdit()

                getter = widget.toPlainText
                setter = lambda value: widget.setPlainText(value)

            else:
                widget = QLineEdit()

                getter = widget.text
                setter = lambda value: widget.setText(value)

            controller = WidgetController(getter, setter)

            def on_changed(value=None):
                controller._on_changed(getter())

            widget.textChanged.connect(on_changed)
            controller.__on_changed = on_changed

        elif type_name == "int":
            widget = QSpinBox()

            getter = widget.value
            setter = lambda value: widget.setValue(value)

            controller = WidgetController(getter, setter)
            widget.valueChanged.connect(controller._on_changed)

        elif type_name == "float":
            widget = QDoubleSpinBox()

            getter = widget.value
            setter = lambda value: widget.setValue(value)

            controller = WidgetController(getter, setter)
            widget.valueChanged.connect(controller._on_changed)

        elif type_name == "bool":
            widget = QCheckBox()

            getter = lambda: bool(widget.isChecked)
            setter = lambda value: widget.setChecked(value)

            controller = WidgetController(getter, setter)
            widget.stateChanged.connect(lambda v: controller._on_changed(bool(v)))

        else:
            widget = QLineEdit()

            getter = lambda: eval(widget.text())
            setter = lambda value: widget.setText(repr(value))

            controller = WidgetController(getter, setter)
            widget.textChanged.connect(controller._on_changed)

            controller.value = None

    return widget, controller
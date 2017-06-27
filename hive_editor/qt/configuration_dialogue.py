from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QGroupBox, QFormLayout, QVBoxLayout, QLabel

from .widgets import create_widget
from ..utils import start_value_from_type


class ConfigurationDialogue(QDialog):
    class NoValue:
        pass

    class DialogueCancelled(Exception):
        pass

    def __init__(self, parent=None):
        super(ConfigurationDialogue, self).__init__(parent)

        buttons_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons_box.accepted.connect(self.accept)
        buttons_box.rejected.connect(self.reject)

        self.form_group_box = QGroupBox("Form layout")

        self.layout = QFormLayout()
        self.form_group_box.setLayout(self.layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.form_group_box)
        main_layout.addWidget(buttons_box)

        self.setLayout(main_layout)

        self.value_getters = {}
        self.values = {}

    def addWidget(self, name, data_type="", default=NoValue, options=None):
        widget, controller = create_widget(data_type, options)

        # If has no default, try and guess one
        if default is self.__class__.NoValue:
            try:
                default = start_value_from_type(data_type)

            except TypeError:
                pass

        # If we have a default, set it
        if default is not self.__class__.NoValue:
            try:
                controller.value = default

            except Exception as err:
                print(err)

        self.layout.addRow(QLabel(name), widget)
        self.value_getters[name] = controller.getter

    def accept(self):
        QDialog.accept(self)

        self.values = {n: v() for n, v in self.value_getters.items()}

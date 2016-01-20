# Import PySide classes
import ctypes
import os
import sys

import editor.qt as any_qt
import editor.qt.qdarkstyle as qdarkstyle

from editor.qt.main_window import MainWindow
from editor.qt.qt_core import *
from editor.qt.qt_gui import *
from editor.qt.qt_webkit import *

if __name__ == "__main__":
    # Create a Qt application
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(pyside=any_qt.IS_PYSIDE))

    # Fix for windows tray icon
    app_id = 'hive2.hive2.1.0'
    try:
        windll = ctypes.windll

    except AttributeError:
        pass

    else:
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    window = MainWindow()
    window.resize(1024, 768)

    window.show()

    # Add Help page
    home_page = QWebView()

    USE_LOCAL_HOME = True

    if USE_LOCAL_HOME:
        # Load Help data
        local_dir = any_qt.__path__[0]
        html_file_name = os.path.join(local_dir, "home.html")

        with open(html_file_name) as f:
            html = f.read().replace("%LOCALDIR%", local_dir)

        home_page.setHtml(html)
    else:
        url = QUrl("https://github.com/agoose77/hive2/wiki")
        home_page.load(url)

    window.load_home_page(home_page)

    # Enter Qt application main loop
    app.exec_()
    sys.exit()

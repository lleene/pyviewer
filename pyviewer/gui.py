"""WIP: Helper module for launching graphical application directly."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from pyviewer import PyViewer


def start_viewer(root_dir):
    """Initialize the QML application and load media in the root_dir."""
    app = QApplication()
    engine = QQmlApplicationEngine()

    pyviewer = PyViewer()
    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")
    pyviewer.load_file_map(".", root_dir)
    pyviewer.path_changed.emit()

    if not engine.rootObjects():
        sys.exit(-1)

    ret = app.exec()
    pyviewer.imageloader.save_tag_filter(".")
    sys.exit(ret)

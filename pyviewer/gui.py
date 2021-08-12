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
    pyviewer.load_file_map(root_dir)

    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")

    print("Done!")
    if not engine.rootObjects():
        sys.exit(-1)

    ret = app.exec()
    sys.exit(ret)

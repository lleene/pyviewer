#!/bin/env python3

import sys
from pyviewer import PyViewer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine


def StartViewer(root_dir):
    print("Starting up...")
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pyviewer = PyViewer()
    pyviewer.loadFileMap(root_dir)

    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")

    print("Done!")
    if not engine.rootObjects():
        sys.exit(-1)

    ret = app.exec()
    pyviewer.imageloader.saveTagFilter()
    pyviewer.imageloader.reportFilterState()
    sys.exit(ret)


if __name__ == "__main__":
    StartViewer(sys.argv[1])

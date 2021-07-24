#!/bin/env python3

import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, QCoreApplication
from PySide2.QtQml import QQmlApplicationEngine


class MainWindow(QApplication):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine("main.qml")
    sys.exit(app.exec_())

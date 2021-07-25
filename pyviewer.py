#!/bin/env python3

import sys
from imageloader import ImageLoader

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QCoreApplication, Qt, QObject, Property, Signal
from PySide2.QtQml import QQmlApplicationEngine


class PyViewer(QObject):
    pathChanged = Signal(str)

    def __init__(self, parent=None):
        super(PyViewer, self).__init__(parent)
        self.imageloader = ImageLoader()
        self._files = " ".join(
            ["data/image" + str(index) + ".png" for index in range(0, 25)]
        )

    def loadFileMap(self, root_dir):
        self.imageloader.loadArtistMap(root_dir)
        file_list = self.imageloader.loadViews()
        self._files = " ".join(self.imageloader.orderFileList(file_list))

    @Property(str, notify=pathChanged)
    def path(self):
        return self._files


def main():
    print("Starting up...")
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pyviewer = PyViewer()
    pyviewer.loadFileMap("/mnt/media/Media/doujin_archive_2")

    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("main.qml")

    print("Done!")
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

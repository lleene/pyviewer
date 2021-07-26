#!/bin/env python3

import sys
from imageloader import ImageLoader

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt, QObject, Property, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine


class PyViewer(QObject):
    pathChanged = Signal()

    def __init__(self, parent=None):
        super(PyViewer, self).__init__(parent)
        self.imageloader = ImageLoader()
        self._files = " ".join(
            ["data/image" + str(index) + ".png" for index in range(0, 25)]
        )

    def extractFiles(self):
        self._files = ""
        self.pathChanged.emit()
        file_list = self.imageloader.extractCurrentIndex()
        self._files = " ".join(self.imageloader.orderFileList(file_list))
        self.pathChanged.emit()

    def loadFileMap(self, root_dir):
        self.imageloader.loadMedia(root_dir)
        self.extractFiles()

    @Property(str, notify=pathChanged)
    def path(self):
        return self._files

    @Slot(int)
    def loadNextArchive(self, direction):
        self.imageloader.artist_index = (
            self.imageloader.artist_index + direction
        ) % len(self.imageloader.artists)
        self.extractFiles()

    @Slot(bool)
    def updateTagFilter(self, filter_bool):
        self.imageloader.updateTagFilter(filter_bool)
        self.extractFiles()

    @Slot()
    def undoLastFilter(self):
        self.imageloader.undoLastFilter()
        self.extractFiles()


def main(root_dir):
    print("Starting up...")
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    pyviewer = PyViewer()
    pyviewer.loadFileMap(root_dir)

    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer.qml")

    print("Done!")
    if not engine.rootObjects():
        sys.exit(-1)

    ret = app.exec()
    pyviewer.imageloader.saveTagFilter()
    pyviewer.imageloader.reportFilterState()
    sys.exit(ret)


if __name__ == "__main__":
    main(sys.argv[1])

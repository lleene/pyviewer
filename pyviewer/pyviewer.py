"""Main QObject with qml bindings that prompt excusion from user interface."""

from PySide6.QtCore import QObject, Property, Signal, Slot
from pyviewer import ImageLoader


class PyViewer(QObject):
    """ """
    pathChanged = Signal()

    def __init__(self, parent=None):
        """ """
        super().__init__(parent)
        self.imageloader = ImageLoader()

    def extractFiles(self):
        self._files = ""
        self.pathChanged.emit()
        file_list = self.imageloader.extractCurrentIndex()
        self._files = "::".join(self.imageloader.orderFileList(file_list))
        self.pathChanged.emit()

    def loadFileMap(self, media_path):
        self.imageloader.loadMedia(media_path)
        self.extractFiles()

    @Property(str, notify=pathChanged)
    def path(self):
        return self._files

    @Slot(int)  # TODO reimplement modulo
    def loadNextArchive(self, direction):
        self.imageloader.index = self.imageloader.index + direction
        self.extractFiles()

    @Slot(bool)
    def updateTagFilter(self, filter_bool):
        self.imageloader.updateTagFilter(filter_bool)
        self.extractFiles()

    @Slot()
    def undoLastFilter(self):
        self.imageloader.undoLastFilter()
        self.extractFiles()

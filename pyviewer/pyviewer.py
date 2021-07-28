from pyviewer import ImageLoader
from PySide6.QtCore import QObject, Property, Signal, Slot


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

"""Main QObject with qml bindings that prompt excusion from user interface."""

import sys
from PySide2.QtCore import QByteArray, QObject, Property, Signal, Slot
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtWidgets import QApplication
from pyviewer import MetaMatcher

class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""
    images_changed = Signal(name="images_changed")

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = MetaMatcher()

    def load_images(self):
        """Prompt loader to extract new set of files and emit change."""
        self.imageloader.extract_current_index()
        self.images_changed.emit()

    def load_file_map(self, media_path):
        """Load media path and refresh viewer."""
        self.imageloader.load_file_map(media_path)
        self.load_images()

    @Property(int)
    def length_images(self):
        """Number of available images."""
        return len(self.imageloader._images)

    @Property(int)
    def length_previews(self):
        """Number of available previews."""
        return len(self.imageloader._previews)

    @Property(str , notify=images_changed)
    def file_name(self):
        """Return extracted image at index."""
        return self.imageloader.media["name"]

    @Property(list , notify=images_changed)
    def meta_data(self):
        """Return extracted image at index."""
        return [ image["title"] for image in self.imageloader._previews if "title" in image ]

    @Property(list , notify=images_changed)
    def images(self):
        """Return extracted image at index."""
        return [ QByteArray(image).toBase64() for image in self.imageloader._images ]

    @Property(list , notify=images_changed)
    def previews(self):
        """Return extracted image at index."""
        return [ QByteArray(image["image"]).toBase64() for image in self.imageloader._previews if "image" in image]

    @Slot(int)
    def load_next_archive(self, direction):
        """Adjust tag index and refresh viewer."""
        self.imageloader.adjust_index(direction)
        self.load_images()

    @Slot(int)
    def set_max_image_count(self, count):
        """Set the maximum number of Images."""
        self.imageloader.max_image_count = count


def start_viewer(media_dir):
    """Initialize the QML application and load media in the root_dir."""
    app = QApplication()
    engine = QQmlApplicationEngine()

    pyviewer = PyViewer()
    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")
    pyviewer.imageloader.load_cache(".")
    pyviewer.load_file_map(media_dir)

    pyviewer.images_changed.emit()
    if not engine.rootObjects():
        sys.exit(-1)
    ret = app.exec_()
    pyviewer.imageloader.save_cache(".")
    sys.exit(ret)

"""Main QObject with qml bindings that prompt excusion from user interface."""

import sys
from PySide6.QtCore import QByteArray, QObject, Property, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from pyviewer import BooruLoader, ImageLoader

class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""
    images_changed = Signal(name="images_changed")

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = ImageLoader()
        # self.imageloader = BooruLoader()

    def load_images(self):
        """Prompt loader to extract new set of files and emit change."""
        self.imageloader.extract_current_index()
        self.images_changed.emit()

    def load_file_map(self, run_dir, media_path):
        """Load media path and refresh viewer."""
        self.imageloader.load_media(run_dir, media_path)
        self.load_images()

    @Property( int )
    def length(self):
        """Number of available images."""
        return len(self.imageloader._images)

    @Property(list , notify=images_changed)
    def images(self):
        """Return extracted image at index."""
        return [ QByteArray(image).toBase64() for image in self.imageloader._images ]

    @Slot(int)
    def load_next_archive(self, direction):
        """Adjust tag index and refresh viewer."""
        self.imageloader.adjust_index(direction)
        self.load_images()

    @Slot(bool)
    def update_tag_filter(self, filter_bool):
        """Store tag result and refresh viewer."""
        self.imageloader.update_tag_filter(filter_bool)
        self.load_images()

    @Slot()
    def undo_last_filter(self):
        """Undo the last tagfilter change and refresh viewer."""
        self.imageloader.undo_last_filter()
        self.load_images()

    @Slot(int)
    def set_max_image_count(self, count):
        """Set the maximum number of Images."""
        self.imageloader.max_image_count = count


def start_viewer(root_dir):
    """Initialize the QML application and load media in the root_dir."""
    app = QApplication()
    engine = QQmlApplicationEngine()

    pyviewer = PyViewer()
    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")
    pyviewer.load_file_map(".", root_dir)
    pyviewer.images_changed.emit()

    if not engine.rootObjects():
        sys.exit(-1)

    ret = app.exec()
    # pyviewer.imageloader.save_tag_filter(".")
    sys.exit(ret)

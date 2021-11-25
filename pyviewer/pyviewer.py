"""Main QObject with qml bindings that prompt excusion from user interface."""

from PySide2.QtCore import QByteArray, QObject, Property, Signal, Slot
from .imageloader import ArchiveBrowser, BooruBrowser


class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = None
        self._image_index = 0

    def load_file_map(self, media_path):
        """Load media path and refresh viewer."""
        self.imageloader = BooruBrowser()

    @Property(int)
    def length_images(self) -> int:
        """Return number of available images."""
        return self.imageloader.count if self.imageloader else 0

    @Property(str)
    def file_name(self) -> str:
        """Return extracted image at index."""
        return self.imageloader.tag if self.imageloader else ""

    @Property(QByteArray)
    def image(self):
        """Return an image at index."""
        return (
            QByteArray(self.imageloader.images[self._image_index]).toBase64()
            if self.imageloader
            else QByteArray().toBase64()
        )

    @Slot(int)
    def index(self, image_index: int):
        """Adjust tag index and refresh viewer."""
        self._image_index = image_index

    @Slot(int)
    def load_next_archive(self, direction):
        """Adjust tag index and refresh viewer."""
        self.imageloader.adjust_index(direction)
        del self.imageloader.images

    @Slot(int)
    def set_max_image_count(self, count):
        """Set the maximum number of Images."""
        if self.imageloader:
            self.imageloader.max_image_count = count


# =]

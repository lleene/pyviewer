"""Main QObject with qml bindings that prompt excusion from user interface."""

import sys
from PySide2.QtCore import QByteArray, QObject, Property, Signal, Slot
from .imageloader import ArchiveBrowser


class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""

    images_changed = Signal(name="images_changed")

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = None

    def load_file_map(self, media_path):
        """Load media path and refresh viewer."""
        self.imageloader = ArchiveBrowser(media_path)
        self.images_changed.emit()

    @Property(int)
    def length_images(self) -> int:
        """Return number of available images."""
        return self.imageloader.count if self.imageloader else 0

    @Property(str, notify=images_changed)
    def file_name(self) -> str:
        """Return extracted image at index."""
        return self.imageloader.tag if self.imageloader else ""

    @Property(list, notify=images_changed)
    def images(self):
        """Return extracted image at index."""
        return (
            [QByteArray(image).toBase64() for image in self.imageloader.images]
            if self.imageloader
            else []
        )

    @Slot(int)
    def load_next_archive(self, direction):
        """Adjust tag index and refresh viewer."""
        self.imageloader.adjust_index(direction)
        del self.imageloader.images
        self.images_changed.emit()

    @Slot(int)
    def set_max_image_count(self, count):
        """Set the maximum number of Images."""
        if self.imageloader:
            self.imageloader.max_image_count = count


# =]

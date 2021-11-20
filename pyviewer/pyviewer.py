"""Main QObject with qml bindings that prompt excusion from user interface."""

import sys
from PySide2.QtCore import QByteArray, QObject, Property, Signal, Slot
from .imageloader import ImageLoader


class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""

    images_changed = Signal(name="images_changed")

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = ImageLoader()

    def load_images(self):
        """Prompt loader to extract new set of files and emit change."""
        self.imageloader.file_list
        self.images_changed.emit()

    def load_file_map(self, media_path):
        """Load media path and refresh viewer."""
        self.imageloader.load_media(
            media_path, "/mnt/media/Media/booru_archive/data/original"
        )

    @Property(int)
    def length_images(self):
        """Return number of available images."""
        return self.imageloader.count

    @Property(str, notify=images_changed)
    def file_name(self):
        """Return extracted image at index."""
        return self.imageloader.tag

    @Property(list, notify=images_changed)
    def images(self):
        """Return extracted image at index."""
        return [
            QByteArray(image).toBase64() for image in self.imageloader._images
        ]

    @Slot(int)
    def load_next_archive(self, direction):
        """Adjust tag index and refresh viewer."""
        self.imageloader.adjust_index(direction)
        self.load_images()

    @Slot(int)
    def set_max_image_count(self, count):
        """Set the maximum number of Images."""
        self.imageloader.max_image_count = count


# =]

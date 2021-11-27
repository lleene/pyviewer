"""Main QObject with qml bindings that prompt excusion from user interface."""

from typing import Union
from PySide6.QtCore import QByteArray, QObject, Property, Signal, Slot
from .imageloader import ArchiveBrowser, BooruBrowser


class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = None
        self._image_index = 0

    def load_media(
        self, imageloader: Union[BooruBrowser, ArchiveBrowser]
    ) -> None:
        """Load media path and refresh viewer."""
        self.imageloader = imageloader

    @Property(int)
    def length_images(self) -> int:
        """Return number of available images."""
        return self.imageloader.count if self.imageloader else 0

    @Property(str)
    def file_name(self) -> str:
        """Return extracted image at index."""
        return self.imageloader.tag if self.imageloader else ""

    @Slot(int)
    def hash(self, image_index: int = 0):
        """Print image hash at index."""
        print(
            f"{self.file_name}: {self.imageloader.path(image_index)}"
            + f" - {self.imageloader.hash(image_index)}"
        )

    @Property(QByteArray)
    def image(self) -> QByteArray:
        """Return an image at index."""
        return (
            QByteArray(self.imageloader.image(self._image_index)).toBase64()
            if self.imageloader
            else QByteArray().toBase64()
        )

    @Slot(int)
    def index(self, image_index: int) -> None:
        """Adjust image index."""
        self._image_index = image_index

    @Slot(int)
    def load_next_archive(self, direction: int) -> None:
        """Adjust tag index and clear image cache."""
        self.imageloader.adjust_index(direction)
        del self.imageloader.files


# =]

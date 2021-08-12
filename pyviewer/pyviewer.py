"""Main QObject with qml bindings that prompt excusion from user interface."""

from PySide6.QtCore import QObject, Property, Signal, Slot
from pyviewer import ImageLoader


class PyViewer(QObject):
    """QObject for binging user interface to imageloader."""
    path_changed = Signal()

    def __init__(self, parent=None):
        """Initialize image loader backend and load defaults."""
        super().__init__(parent)
        self.imageloader = ImageLoader()
        self._files = ""

    def extract_files(self):
        """Prompt loader to extract new set of files and emit change."""
        self._files = ""
        self.path_changed.emit()
        self._files = "::".join(self.imageloader.file_list)
        self.path_changed.emit()

    def load_file_map(self, media_path):
        """Load media path and refresh viewer."""
        self.imageloader.load_media(media_path, media_path)
        self.extract_files()

    @Property(str, notify=path_changed)
    def path(self):
        """Compound string concaternating currently extracted images."""
        return self._files

    @Slot(int)
    def load_next_archive(self, direction):
        """Adjust tag index and refresh viewer."""
        self.imageloader.adjust_index(direction)
        self.extract_files()

    @Slot(bool)
    def update_tag_filter(self, filter_bool):
        """Store tag result and refresh viewer."""
        self.imageloader.update_tag_filter(filter_bool)
        self.extract_files()

    @Slot()
    def undo_last_filter(self):
        """Undo the last tagfilter change and refresh viewer."""
        self.imageloader.undo_last_filter()
        self.extract_files()

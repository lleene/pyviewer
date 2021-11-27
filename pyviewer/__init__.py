"""Top-level package for pyviewer."""

__author__ = """Lieuwe Leene"""
__email__ = "lieuwe@leene.dev"
__version__ = "0.2.1"

from .util import TagManager
from .imageloader import ArchiveBrowser, BooruBrowser
from .pyviewer import PyViewer

__all__ = (
    "ArchiveBrowser",
    "BooruBrowser",
    "PyViewer",
    "TagManager",
)

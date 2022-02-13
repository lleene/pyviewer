"""Console script for pyviewer."""
import os
import sys
import logging
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from pyviewer import PyViewer, __version__, ArchiveBrowser, BooruBrowser


def setup_logger(setup: ArgumentParser) -> None:
    # TODO reconfigure properly
    """Setup Logging."""
    log_level = [
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
    ][max(0, min(3, setup.level))]
    logging.basicConfig()
    logging.getLogger().setLevel(log_level)
    logging.debug(f"{setup.__repr__()}")


def pyviewer_parser() -> ArgumentParser:
    """Argparse configuration for running RdbDoc from the command line."""
    parser = ArgumentParser(
        prog="pyviewer",
        description=f"PyViewer {__version__}: A pyside based image browser "
        + "for compressed archives and booru databases.",
    )
    source_selection = parser.add_mutually_exclusive_group()
    source_selection.add_argument(
        "-a",
        "--archive",
        dest="archive",
        type=Path,
        metavar="PATH",
        help="Browse collection of compressed archives."
        + " Must specify a valid path.",
        default=None,
    )
    source_selection.add_argument(
        "-b",
        "--booru",
        dest="booru",
        type=str,
        metavar="HOST",
        help="Browse booru host with tagged image database."
        + " Must specify a valid host address.",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--tags",
        type=str,
        dest="tags",
        nargs="+",
        metavar="TAGS",
        help="Browse selected tags.",
        default=None,
    )
    parser.add_argument(
        "-r",
        "--reload",
        dest="reload",
        action="store_true",
        default=False,
        help="Reload media to state file.",
    )
    parser.add_argument(
        "-s",
        "--state",
        nargs="?",
        dest="state",
        type=Path,
        metavar="SAVE",
        help="Save viewer state to file.",
        default=NamedTemporaryFile(mode="w").name,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="level",
        action="count",
        default=0,
        help="Pring debug information.",
    )
    return parser


def start_viewer(setup) -> int:
    """Initialize the QML application and load media in the root_dir."""
    pyviewer = PyViewer()
    if setup.archive:
        logging.debug("Setting up ArchiveBrowser.")
        pyviewer.load_media(
            ArchiveBrowser(
                os.path.realpath(setup.archive),
                state_file=setup.state,
                tags=setup.tags,
                reload=setup.reload,
            )
        )
    else:
        logging.debug("Setting up BooruBrowser.")
        pyviewer.load_media(
            BooruBrowser(
                setup.booru,
                state_file=setup.state,
                tags=setup.tags,
                reload=setup.reload,
            )
        )
    if not pyviewer.imageloader.count:
        print("No media found, exiting...")
        return 1
    logging.debug("Loading QML Objects.")
    app = QApplication()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("viewer", pyviewer)
    qml_file = os.path.join(os.path.dirname(__file__), "pyviewer.qml")
    engine.load(QUrl(qml_file))
    logging.debug("Launching PyViewer.")
    if not engine.rootObjects():
        return 1
    return app.exec()


def main() -> int:
    """Console script for pyviewer."""
    parser = pyviewer_parser()
    setup = parser.parse_args()
    setup_logger(setup)
    return start_viewer(setup)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

"""Console script for pyviewer."""
import os
import sys
from pathlib import Path
from ipaddress import ip_address
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from pyviewer import PyViewer, __version__, ArchiveBrowser, BooruBrowser


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
        type=Path,
        metavar="PATH",
        help="Browse collection of compressed archives."
        + " Must specify a valid path.",
        default=None,
    )
    source_selection.add_argument(
        "-b",
        "--booru",
        type=ip_address,
        metavar="HOST",
        help="Browse booru host with tagged image database."
        + " Must specify a valid host address.",
        default=None,
    )
    parser.add_argument(
        "--tags",
        "-t",
        type=str,
        nargs="+",
        metavar="TAGS",
        help="Browse selected tags",
        default=None,
    )
    parser.add_argument(
        "--state",
        "-s",
        nargs="?",
        type=Path,
        metavar="SAVE",
        help="Save viewer state to file",
        default=NamedTemporaryFile(mode="w").name,
    )
    return parser


def start_viewer(setup: ArgumentParser) -> int:
    """Initialize the QML application and load media in the root_dir."""
    app = QApplication()
    engine = QQmlApplicationEngine()
    pyviewer = PyViewer()
    if setup.archive:
        pyviewer.load_media(
            ArchiveBrowser(
                os.path.realpath(setup.archive),
                state_file=setup.state,
                tags=setup.tags,
            )
        )
    else:
        pyviewer.load_media(
            BooruBrowser(setup.booru, state_file=setup.state, tags=setup.tags)
        )
    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")
    if not engine.rootObjects():
        return 1
    return app.exec()


def main() -> int:
    """Console script for pyviewer."""
    try:
        sys.argv = [
            unicode(arg.decode(sys.stdin.encoding)) for arg in sys.argv
        ]
    except (NameError, TypeError):
        pass
    except UnicodeDecodeError:
        return 1
    parser = pyviewer_parser()
    setup = parser.parse_args(sys.argv[1:])
    return start_viewer(setup)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

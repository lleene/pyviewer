"""Console script for pyviewer."""
import os
import sys
import argparse
from pathlib import Path

from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtWidgets import QApplication
from pyviewer import PyViewer, __version__


def start_viewer(media_dir):
    """Initialize the QML application and load media in the root_dir."""
    app = QApplication()
    engine = QQmlApplicationEngine()
    pyviewer = PyViewer()
    engine.rootContext().setContextProperty("viewer", pyviewer)
    engine.load("pyviewer/pyviewer.qml")
    pyviewer.load_file_map(media_dir)
    pyviewer.images_changed.emit()
    if not engine.rootObjects():
        sys.exit(-1)
    ret = app.exec_()
    sys.exit(ret)


def pyviewer_parser():
    """Argparse configuration for running RdbDoc from the command line."""
    parser = argparse.ArgumentParser(
        prog="pyviewer",
        description=f"PyViewer {__version__}: A pyside based image browser "
        + "for compressed archives and booru databases.",
    )
    parser.add_argument(
        "media",
        type=Path,
        help="Path to media dir root.",
    )
    return parser


def main():
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
    start_viewer(os.path.realpath(setup.media))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

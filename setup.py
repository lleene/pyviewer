# -*- coding utf-8 -*-
# !/usr/bin/env python

# setuptools imports
from setuptools import setup
from setuptools import find_packages

# pyviewer imports
from pyviewer import __version__, __author__, __email__

# Read requirements file
with open("requirements.txt") as f:
    requirements = [l for l in f.read().splitlines() if l]

# Read description file
with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="pyviewer",
    version=__version__,
    packages=find_packages(),
    author=__author__,
    author_email=__email__,
    keywords=["image-viewer", "qml", "pyside6"],
    description="Simple pyside6 image browser for archived folders",
    long_description=long_description(),
    url="https://github.com/lleene/pyviewer",
    download_url="https://github.com/lleene/pyviewer/tarball/master",
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pyviewer = pyviewer.command:main",
        ]
    },
    license="MIT",
)

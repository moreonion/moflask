#!/usr/bin/env python

"""Package meta data for moflask."""

from setuptools import setup

setup(
    name="moflask",
    version="1.0b1",
    description="Re-usable flask utilities.",
    author="Roman Zimmermann",
    author_email="torotil@gmail.com",
    packages=["moflask"],
    install_requires=[
        "Flask>=1.1",
        "python-json-logger",
    ],
    extras_require={
        "test": ["pytest", "python-json-logger"],
        "requests": ["requests"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    url="https://github.com/moreonion/moflask",
    download_url="https://github.com/moreonion/moflask/archive/v0.1.tar.gz",
)

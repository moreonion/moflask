#!/usr/bin/env python

"""Package meta data for moflask."""

import setuptools

setuptools.setup(
    name="moflask",
    version="1.1.0",
    description="Re-usable flask utilities.",
    author="Roman Zimmermann",
    author_email="torotil@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "Flask>=1.1",
        "python-json-logger",
    ],
    extras_require={
        "test": ["pytest", "python-json-logger"],
        "requests": ["requests"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    url="https://github.com/moreonion/moflask",
    download_url="https://github.com/moreonion/moflask/archive/refs/tags/v1.1.0.tar.gz",
)

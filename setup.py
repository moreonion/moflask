#!/usr/bin/env python

"""Package meta data for moflask."""

import setuptools

setuptools.setup(
    name="moflask",
    version="1.2.1",
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
        "jwt": ["flask-jwt-extended"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        "pytest11": [
            "moflask = moflask.pytest_plugin",
        ],
    },
    url="https://github.com/moreonion/moflask",
    download_url="https://github.com/moreonion/moflask/archive/refs/tags/v1.2.1.tar.gz",
)

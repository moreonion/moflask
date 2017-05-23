#!/usr/bin/env python

from distutils.core import setup

setup(
    name='moflask',
    version='0.1',
    description='Re-usable flask utilities.',
    author='Roman Zimmermann',
    author_email='torotil@gmail.com',
    packages=['moflask'],
    install_requires=['Flask'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    url='https://github.com/moreonion/moflask',
    download_url='https://github.com/moreonion/moflask/archive/v0.1.tar.gz',
)

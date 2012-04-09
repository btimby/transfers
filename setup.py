#!/bin/env python

from distutils.core import setup

name = 'transfers'
version = '0.1'
release = '1'
versrel = version + '-' + release
download_url = 'https://github.com/downloads/btimby/' + name + \
                           '/' + name + '-' + versrel + '.tar.gz'
description = """\
"""


setup(
    name = name,
    version = versrel,
    description = 'FTP for Humans.',
    long_description = description,
    author = 'Ben Timby',
    author_email = 'btimby@gmail.com',
    maintainer = 'Ben Timby',
    maintainer_email = 'btimby@gmail.com',
    url = 'http://github.com/btimby/' + name + '/',
    download_url = download_url,
    license = 'GPLv3',
    packages = ["transfers"],
    classifiers = (
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Networking',
          'Topic :: Internet :: File Transfer Protocol (FTP)',
    ),
)

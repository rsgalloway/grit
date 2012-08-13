#!/usr/bin/env python
#
# Copyright (C) 2011-2012 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Grit and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

import os
from setuptools import setup

def get_packages(path):
    packages = []
    for (path, dirs, files) in os.walk(path):
        packages.append(path)
    return packages

setup(
    name='grit',
    author='Ryan Galloway',
    author_email='ryan@rsgalloway.com',
    version='0.1',
    description='Grit is a simple git repo manager with limited remote object proxying, a http back-end and simple cli.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='http://www.github.com/rsgalloway/grit',
    license='New BSD License',
    keywords = "git repo manager remote object proxy",
    platforms=['OS Independent'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    zip_safe=False,
    packages=get_packages('grit') + get_packages('static'),
    scripts=['bin/grit'],
    package_data = {
        '': ['*.py', '*.html', '*.css', '*.js', '*.png', '*.gif', '*.ico'],
    }
)

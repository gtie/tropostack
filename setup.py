#!/usr/bin/env python
import io
import os
import re

from setuptools import find_packages
from setuptools import setup
from distutils.util import convert_path

def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return re.sub(text_type(r':[a-z]+:`~?(.*?)`'), text_type(r'``\1``'), fd.read())

def load_pkg_init():
    result = {}
    init_path = convert_path('tropostack/__init__.py')
    with open(init_path) as init_file:
        exec(init_file.read(), result)
    return result
PKG_INIT = load_pkg_init()

setup(
    name="tropostack",
    version=PKG_INIT['version'],
    url="https://github.com/topostack/tropostack",
    license='MIT',
    author="tie",
    author_email="tropostack@morp.org",
    description=PKG_INIT['__doc__'].strip(),
    long_description_content_type='text/x-rst',
    long_description=read("README.rst"),
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        'boto3',
        'tabulate',
        'troposphere',
        'pyyaml',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)

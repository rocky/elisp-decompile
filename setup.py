import sys
from setuptools import setup

classifiers = [
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
]

VERSION = "?.?.?" # To make Python happy
# This re-initializes VERSION

import os.path
def get_srcdir():
    filename = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    return os.path.realpath(filename)

srcdir = get_srcdir()

def read(*rnames):
    return open(os.path.join(srcdir, *rnames)).read()

exec(read('lapdecompile/version.py'))

if sys.version_info < (3, 7):
    sys.exit("Sorry, Python < 3.7 is not supported")

setup(
    author="Rocky Bernstein",
    author_email = "rb@dustyfeet.com",
    install_requires=("spark_parser>=1.8.9",),
    name="lapdecompile",
    description="A decompiler for Emacs Lisp bytecode",
    long_description="""
A decompiler for Emacs Lisp bytecode.

This is in a very early stage, but amazingly the code seems sound so far. Please join
in and help.
""",
    entry_points={"console_scripts": ["lap-decompile   = lapdecompile.main:main"]},
    version=VERSION,
    url="https://github.com/rocky/elisp-decompile",
)

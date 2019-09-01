import sys
from setuptools import setup

classifiers = [
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
]

if sys.version_info < (3, 7):
    sys.exit("Sorry, Python < 3.7 is not supported")

setup(
    author="Rocky Bernstein",
    install_requires=("spark_parser>=1.8.9",),
    name="lapdecompile",
    entry_points={"console_scripts": ["lap-decompile   = lapdecompile.main:main"]},
)

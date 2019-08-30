from setuptools import setup
classifiers =  [
                'Intended Audience :: Developers',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Programming Language :: Python :: 3.7',
                ]

setup(
    author            = "Rocky Bernstein",
    install_requires  = ('spark_parser>=1.8.9',),
    name = 'eldecompile',
    entry_points = {
        'console_scripts': [
            'eldecompile   = eldecompile.main:main',
       ]},
    )

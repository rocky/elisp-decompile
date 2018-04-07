from setuptools import setup
classifiers =  [
                'Intended Audience :: Developers',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: 3.3',
                'Programming Language :: Python :: 3.4',
                'Programming Language :: Python :: 3.5',
                'Programming Language :: Python :: 3.6',
                ]

setup(
    author            = "Rocky Bernstein",
    install_requires  = ('spark_parser>=1.8.5',),
    name = 'eldecompile',
    entry_points = {
        'console_scripts': [
            'eldecompile   = eldecompile.main:main',
       ]},
    )

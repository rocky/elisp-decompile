#!/usr/bin/env python
from spark_parser.ast import AST

from eldecompile.scanner import fn_scanner
from eldecompile.parser import ElispParser
from eldecompile.semantics import SourceWalker

import sys

if len(sys.argv) == 2:
    path = sys.argv[1]
else:
    # path = 'binops.dis'
    # path = 'control.dis'
    path = 'unary-ops.dis'

with open(path, 'r') as fp:
    header, fn_args, tokens = fn_scanner(fp)
    pass

p = ElispParser(AST)
parser_debug = {'rules': False, 'transition': False, 'reduce' : True,
               'errorstack': 'full', 'dups': False }

ast = p.parse(tokens, debug=parser_debug)
print(ast)
formatter = SourceWalker(ast)
result = formatter.traverse(ast)
print(result)

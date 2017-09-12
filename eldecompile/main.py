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

# Scan...
with open(path, 'r') as fp:
    fn_def, tokens = fn_scanner(fp)
    pass

# Parse...
p = ElispParser(AST)
parser_debug = {'rules': False, 'transition': False, 'reduce' : True,
               'errorstack': 'full', 'dups': False }

ast = p.parse(tokens, debug=parser_debug)
print(ast)

# .. and Generate Elisp
formatter = SourceWalker(ast)
indent = '  '
result = formatter.traverse(ast, indent)
print("(defun %s%s%s\n%s%s)" %
      (fn_def.name, fn_def.args, fn_def.docstring, indent, result))

"""Scanner for ELISP decompiler

We take input from ELISP disassembly
"""
import re
from eldecompile.tok import Token
from collections import namedtuple

FuncDef = namedtuple('FuncDef', ['name', 'args', 'opt_args', 'docstring'])

def fn_scanner(fp, show_tokens=True):
    tokens = []
    lines = fp.readlines()
    line = lines[0]
    m = re.match("^byte code for (\S+):$", line)
    if m:
        name = m.group(1)
    else:
        name = 'unknown'

    line = lines[1]
    m = re.match("^  args: (\([^)]\))", line)
    if m:
        args = m.group(1)
    else:
        args = '(?)'

    fn_def = FuncDef(name, args, None, None)
    for i, line in enumerate(lines[2:]):
        fields = line.split()
        offset = fields[0]
        colon_point = offset.find(':')
        if colon_point >= 0:
            label = offset[colon_point:]
            offset = offset[:colon_point]
            tokens.append(Token('LABEL', label, offset))
        if fields[1] == 'constant':
            attr = line[line.index(' '):].strip()
            tokens.append(Token('CONSTANT', attr, offset.strip()))
        elif len(fields) == 3:
            offset, opname, attr = fields
            if opname == 'call':
                opname  = "call_%s" % attr
            tokens.append(Token(opname.upper().strip(), attr.strip(), offset.strip()))
        elif len(fields) == 2:
            offset, opname = fields
            tokens.append(Token(opname.upper().strip(), None, offset.strip()))
            pass
        else:
            print("Can't handle line %d:\n\t%s" % (i, line))
        pass

    if show_tokens:
        print(''.join([str(t) for t in tokens]))
    return fn_def, tokens

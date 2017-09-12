"""Scanner for ELISP decompiler

We take input from ELISP disassembly
"""
from eldecompile.tok import Token
def fn_scanner(fp):
    tokens = []
    lines = fp.readlines()
    header = lines[0]
    fn_args = lines[1]
    for i, line in enumerate(lines[2:]):
        fields = line.split()
        if fields[0] == 'constant':
            attr = line[line.index(' '):].strip()
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
    return header, fn_args, tokens

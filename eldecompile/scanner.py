"""Scanner for ELISP decompiler

We take input from ELISP disassembly
"""
from eldecompile.tok import Token
def fn_scanner(fp, show_tokens=True):
    tokens = []
    lines = fp.readlines()
    header = lines[0]
    fn_args = lines[1]
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
    return header, fn_args, tokens

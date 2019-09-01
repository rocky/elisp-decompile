"""Elisp bytecode instruction class. The name "token" reflects our
compiler-centric terminology.
"""
class Token:
    """
    Class representing a byte-code instruction.
    """
    def __init__(self, opname, attr=None, offset=-1,
                 op=None, label=None):
        self.kind = opname
        self.op = op
        self.attr = attr
        self.offset = offset
        self.label = label

    def __eq__(self, o):
        """ '==', but it's okay if offset is different"""
        if isinstance(o, Token):
            # Both are tokens: compare type and attr
            # It's okay if offsets are different
            return (self.kind == o.kind)
        else:
            return self.kind == o

    def __repr__(self):
        return str(self.kind)

    def __repr1__(self, indent, sib_num=''):
        return self.format(line_prefix=indent, sib_num=sib_num)

    def __str__(self):
        return self.format(line_prefix='')

    def format(self, line_prefix='', sib_num=None):
        if sib_num:
            sib_num = "%d." % sib_num
        else:
            sib_num = ''
        prefix = ('%s%s' % (line_prefix, sib_num))
        offset_opname = '%5s %-10s' % (self.offset, self.kind)
        if not self.attr:
            return "%s%s" % (prefix, offset_opname)
        return "%s%s %s" % (prefix, offset_opname,  self.attr)

    def __hash__(self):
        return hash(self.kind)

    def __getitem__(self, i):
        raise IndexError

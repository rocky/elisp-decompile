import re
class Token:
    """
    Class representing a byte-code instruction.
    """
    def __init__(self, opname, attr=None, offset=-1,
                 op=None):
        self.type = intern(opname)
        self.op = op
        self.attr = attr
        self.offset = offset

    def __eq__(self, o):
        """ '==', but it's okay if offset is different"""
        if isinstance(o, Token):
            # Both are tokens: compare type and attr
            # It's okay if offsets are different
            return (self.type == o.type)
        else:
            return self.type == o

    def __repr__(self):
        return str(self.type)

    def __str__(self):
        return self.format(line_prefix='')

    def format(self, line_prefix=''):
        prefix = ('\n%s ' % (line_prefix))
        offset_opname = '%10s  %-10s' % (self.offset, self.type)
        if not self.attr:
            return "%s%s" % (prefix, offset_opname)
        return "%s%s %s" % (prefix, offset_opname,  self.attr)

    def __hash__(self):
        return hash(self.type)

    def __getitem__(self, i):
        raise IndexError

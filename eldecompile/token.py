import re
class Token:
    """
    Class representing a byte-code instruction.
    """
    def __init__(self, type_, attr=None, offset=-1,
                 op=None, has_arg=None):
        self.type = intern(type_)
        self.op = op
        self.has_arg = has_arg
        self.attr = attr
        self.offset = offset
        if has_arg is False:
            self.attr = None

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
        offset_opname = '%10s  %-17s' % (self.offset, self.type)
        if not self.has_arg:
            return "%s%s" % (prefix, offset_opname)
        argstr = "%6d " % self.attr if isinstance(self.attr, int) else (' '*7)
        if re.search('_\d+$', self.type):
            return "%s%s%s" % (prefix, offset_opname,  argstr)
        return "%s%s%s" % (prefix, offset_opname,  argstr)

    def __hash__(self):
        return hash(self.type)

    def __getitem__(self, i):
        raise IndexError

STACK_EFFECT = {
    'add1':            0,
    'bobp':           +1,
    'bolp':           +1,
    'call_1':         -1, # Generalize by preprocessing
    'call_2':         -2,
    'call_3':         -3,
    'call_4':         -4,
    'call_5':         -5,
    'call_6':         -6,
    'call_7':         -7,
    'call_8':         -8,
    'call_9':         -9,
    'call_10':        -10,
    'car':             0,
    'car-safe':        0,
    'cdr':             0,
    'cdr-safe':        0,
    'come_from':       0,
    'concat_2':       -1, # Generalize by preprocessing
    'concat_3':       -2,
    'concat_4':       -3,
    'concatn_5':      -4,
    'concatn_6':      -5,
    'concatn_7':      -6,
    'cons':           -1,
    'constant':       +1,
    'current-buffer': +1,
    'current-column': +1,
    'diff':           -1,
    'discard':        -1,
    'dup':            +1,
    'end-of-line':     0,
    'eobp':           +1,
    'eolp':           +1,
    'eq':             -1,
    'eqlsign':        -1,
    'following-char': +1,
    'goto':           -1,
    'goto-if-nil':    -1,
    'goto-if-nil-else-pop': (-1, 0),
    'goto-if-not-nil': -1,
    'gtr':            -1,
    'insert':          0,
    'integerp':        0,
    'label':           0,
    'leq':            -1,
    'list_1':          0,  # Generalize by preprocessing
    'list_2':         -1,
    'list_3':         -2,
    'list_4':         -3,
    'listn_5':        -4,
    'lss':            -1,
    'max':            -1,
    'min':            -1,
    'not':             0,
    'plus':           -1,
    'point':          +1,
    'point-max':      +1,
    'point-min':      +1,
    'preceding-char': +1,
    'quo':            -1,
    'rem':            -1,
    'return':         -1,
    'save-current-buffer': 0,
    'save-excursion':  0,
    'save-window-excursion': -1,
    'set':            -1,
    'set-buffer':      0,
    'stack-ref':      +1,
    'sub1':            0,
    'unbind':          0,
    'varbind':        -1,
    'varref':         +1,
    'varset':         -1,
    'widen':          +1,

}

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

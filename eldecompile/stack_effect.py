"""Compute eval stack effects in running bytecode instructions
"""

STACK_EFFECTS = {
    'add1':           (-1, +1),
    'bobp':           (-2, +1),
    'bolp':           ( 0, +1),

    # FIXME: Our calls seem to be one off from elisp, because we
    # are counting the function name. so call_1 is elisp call[0]
    'call_1':         (-1, +1), # Generalize by preprocessing
    'call_2':         (-2, +1),
    'call_3':         (-3, +1),
    'call_4':         (-4, +1),
    'call_5':         (-5, +1),
    'call_6':         (-6, +1),
    'call_7':         (-7, +1),
    'call_8':         (-8, +1),
    'call_9':         (-9, +1),
    'call_10':       (-10, +1),
    'car':            (-1, +1),
    'car-safe':       (-1, +1),
    'cdr':            (-1, +1),
    'cdr-safe':       (-1, +1),
    'come_from':      (-0, +0), # A pseudo instruction
    'concat_2':       (-2, +1), # Generalize by preprocessing
    'concat_3':       (-2, +1),
    'concat_4':       (-3, +1),
    'concatn_5':      (-4, +1),
    'concatn_6':      (-5, +1),
    'concatn_7':      (-6, +1),
    'cons':           (-2, +1),
    'consp':          (-1, +1),
    'constant':       (-0, +1),
    'current-buffer': (-0, +1),
    'current-column': (-0, +1),
    'diff':           (-2, +1),
    'discard':        (-1, +0),
    'dup':            (-0, +1),
    'end-of-line':    (-1, +0),
    'eobp':           (-0, +1),
    'eolp':           (-0, +1),
    'eq':             (-2, +1),
    'eqlsign':        (-2, +1),
    'following-char': (-0, +1),
    'goto':           (-0, +0),
    'goto-if-nil':    (-1, +0),
    'goto-if-nil-else-pop': ((-1, -1), (0, 1)),
    'goto-if-not-nil-else-pop': ((-1, -1), (0, 1)),
    'goto-if-not-nil': (-1, +0),
    'gtr':            (-2, +1),
    'insert':         (-1, +1),
    'integerp':       (-1, +1),
    'label':          (-0, +0), # A pseudo instruction
    'leq':            (-2, +1),
    'list_1':         (-1, +1), # Generalize by preprocessing
    'list_2':         (-2, +1),
    'list_3':         (-3, +1),
    'list_4':         (-4, +1),
    'listn_5':        (-5, +1),
    'lss':            (-2, +1),
    'max':            (-2, +1),
    'min':            (-2, +1),
    'not':            (-1, +1),
    'plus':           (-2, +1),
    'point':          (-0, +1),
    'point-max':      (-0, +1),
    'point-min':      (-0, +1),
    'preceding-char': (-0, +1),
    'quo':            (-2, +1),
    'rem':            (-2, +1),
    'return':         (-1, +0),
    'save-current-buffer': (-0, +1),
    'save-excursion':  (-0, +0),
    'save-window-excursion': (-1, +0),
    'set':            (-2, +1),
    'set-buffer':     (-1, +1),
    'stack-ref':      (-0, +1),
    'stack-access':   (-0, +0), # A pseudo instruction
    'sub1':           (-1, +1),
    'unbind':         (-0, +0),
    'varbind':        (-0, +1),
    'varref':         (-0, +1),
    'varset':         (-1, +0),
    'widen':          (-0, +1),

}

STACK_EFFECT = {}
for k, v in STACK_EFFECTS.items():
    if isinstance(v[0], tuple):
        STACK_EFFECT[k] = (v[0][0] + v[1][0], (v[0][1] + v[1][1]))
    else:
        STACK_EFFECT[k] = v[0] + v[1]
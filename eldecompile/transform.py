from __future__ import print_function

import re
from spark_parser import GenericASTTraversal

TRANSFORM = {
    ("call_exprn", 4): ('name_expr', 0),
    ("call_exprn", 5): ('name_expr', 0)
}

def emacs_key_translate(s):
    result = ''
    if s[0] == '"':
        result = '"'
        for c in s[1:]:
            if ord(c) < 31:
                result += '\C-%s' % chr(ord('a') + ord(c) - 1)
            else:
                result += c
                pass
            pass
    else:
        m = re.match("^\[(\w+(?: \w+)*)\]$", s)
        if m:
            for s in m.group(1).split():
                try:
                    i = int(s)
                    if i == 27:
                        result += ' ESC'
                    elif 134217728 <= i <= 134217759:
                        result += ' C-M-%s' % chr(95 - (134217759 - i)).lower()
                    elif 134217761 <= i <= 134217854:
                        result += ' M-%s' % chr(126 - (134217854 - i)).lower()
                except ValueError:
                    # FIXME: check that is something like "right" "up", etc.
                    # Also handle <C-M-down>
                    result += (' <%s>' % s)

    if result != s:
        return 'kbd("%s")' % result.lstrip(' ')
    return s


def emacs_key_normalize(name_expr_node):
    const_node = name_expr_node[0]
    s = const_node.attr
    result = emacs_key_translate(s)
    if result != s:
        const_node.kind = 'TSTRING'
        const_node.attr = result.lstrip(' ')

class TransformTree(GenericASTTraversal, object):
    def __init__(self, ast, debug=False):
        GenericASTTraversal.__init__(self, ast=None)
        self.traverse(ast)
        return

    def default(self, node):
        if not hasattr(node, '__len__'):
            return
        l = len(node)
        key = (node.kind, l)

        if key in TRANSFORM:
            entry = TRANSFORM[key]
            name = "n_%s_%d_%s_%d" % (node.kind, l, entry[0], entry[1])
            if hasattr(self, name):
                func = getattr(self, name)
                func(node)
            self.prune()


    def n_call_exprn_4_name_expr_0(self, call_node):
        assert call_node[0][0] == 'name_expr'
        name_expr = call_node[0][0]
        fn_name = name_expr[0]
        if ( fn_name == 'CONSTANT' and
             fn_name.attr in frozenset(['global-set-key', 'local-set-key']) ):
            key_expr = call_node[1][0]
            if  key_expr == 'name_expr' and key_expr[0] == 'CONSTANT':
                emacs_key_normalize(key_expr)
                pass
            pass
        return

    def n_call_exprn_5_name_expr_0(self, call_node):
        assert call_node[0][0] == 'name_expr'
        name_expr = call_node[0][0]
        fn_name = name_expr[0]
        if ( fn_name == 'CONSTANT' and
             fn_name.attr == 'define-key'):
            key_expr = call_node[2][0]
            if  key_expr == 'name_expr' and key_expr[0] == 'CONSTANT':
                emacs_key_normalize(key_expr)
                pass
            pass
        return

    def traverse(self, node):
        self.preorder(node)

if __name__ == '__main__':
    for seq in (
            """
            [134217761]
            [134217854]
            [134217728]
            [134217729]
            [134217730]
            [134217759]
            [134217820]
            [134217822]
            [134217843|27]
            [27|right]
            """.split()
            ):
        print("'%s' -> '%s'" % (seq,  emacs_key_translate(seq.strip().replace('|', ' '))))

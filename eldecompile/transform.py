from __future__ import print_function

import re
from spark_parser import GenericASTTraversal

TRANSFORM = {
    ("call_exprn", 4): ('name_expr', 0)
}

def emacs_key_normalize(const_node):
    s = const_node[0].attr
    result = s
    if s[0] == '"':
        result = '"'
        for c in s[1:]:
            if ord(c) < 31:
                result += '\C-%s' % chr(ord('a') + ord(c) - 1)
            else:
                result += c
                pass
            pass
        const_node.kind = 'TSTRING'
    else:
        m = re.match("^\[(\d+)\]$", s)
        if m:
            i = int(m.group(1))
            if 134217728 <= i <= 134217759:
                # FIXME: not quite right
                result = '(kbd "C-M-%s")' % chr(134217759 - i + ord('!'))
                const_node.kind = 'TSTRING'
            elif 134217761 <= i <= 134217854:
                try:
                    result = '(kbd "M-%s")' % chr(159 - (134217854 - i + ord('!')))
                except:
                    from trepan.api import debug; debug()
                const_node.kind = 'TSTRING'

    if result != s:
        const_node.attr = result

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

    def traverse(self, node):
        self.preorder(node)

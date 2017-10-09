from __future__ import print_function

from spark_parser import GenericASTTraversal

TRANSFORM = {
    ("call_exprn", 4): ('name_expr', 0)
}

def emacs_key_normalize(s):
    result = ''
    for c in s:
        if ord(c) < 26:
            result += 'C-%s' % chr(ord('a') + ord(c) -1)
        else:
            result += c
    return result

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
                key_expr[0].attr = emacs_key_normalize(key_expr[0].attr)
                pass
            pass
        return

    def traverse(self, node):
        self.preorder(node)

from __future__ import print_function

import re
from copy import copy
from spark_parser import GenericASTTraversal, GenericASTBuilder, GenericASTTraversalPruningException
from eldecompile.tok import Token
from eldecompile.treenode import SyntaxTree


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
        self.debug = debug
        GenericASTTraversal.__init__(self, ast=None)
        return

    @staticmethod
    def unop_operator(node):
        return node[0].kind

    @staticmethod
    def binop_operator(node):
        return node[2][0].kind

    def preorder(self, node=None):
        """Walk the tree in roughly 'preorder' (a bit of a lie explained below).
        For each node with typestring name *name* if the
        node has a method called n_*name*, call that before walking
        children.

        In typical use a node with children can call "preorder" in any
        order it wants which may skip children or order then in ways
        other than first to last.  In fact, this this happens.  So in
        this sense this function not strictly preorder.
        """
        if node is None:
            node = self.ast

        try:
            name = "n_" + self.typestring(node)
            if hasattr(self, name):
                func = getattr(self, name)
                node = func(node)
        except GenericASTTraversalPruningException:
            return

        for i, kid in enumerate(node):
            node[i] = self.preorder(kid)
        return node

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


    def n_unary_expr(self, node):
        binary_expr = node[0][0]
        if not (node[0] == 'expr' and binary_expr in ("binary_expr", "binary_expr_stacked")):
            return node
        binary_op = self.binop_operator(binary_expr)
        unary_op = self.unop_operator(node[1])
        if unary_op == "NOT" and binary_op == "EQLSIGN":
            binary_expr[2][0].kind = "NEQLSIGN"
            node = SyntaxTree(
                node[0][0].kind,  binary_expr, transformed_by="n_" + node.kind,
                )
        return node

    def n_binary_expr(self, node):
        # Flatten f(a (f b))
        expr = node[0]
        fn_name = node[2][0].kind
        if fn_name not in ('MIN', 'MAX'):
            return node
        if expr[0] and expr[0] == 'binary_expr':
            fn_name2 = expr[0][2][0].kind
        else:
            node.transformed_by = "n_" + node.kind
            return node

        if fn_name == fn_name2:
            args = [expr[0][0], expr[0][1], node[1]]
            nt_name = fn_name.lower() + '_exprn'
            node.kind = nt_name
            node.transformed_by = "n_" + node.kind
            node[:len(args)] = args
            pass
        return node

    def n_unary_expr(self, node):
        assert node[0] == "expr"
        expr = node[0]
        unary_op1 = self.unop_operator(node[1])
        if expr[0] == "unary_expr":
            unary_op2 = self.unop_operator(expr[0][1])
            # Handle (cxr (xyr ... )) -> (cxyr ...)
            # FIXME: We combine only two functions. subr.el has up to 4 levels
            if re.match("C[AD]R", unary_op1) and re.match("C[AD]R", unary_op2):
                c12r = f"C%s%sR" % (unary_op1[1:2], unary_op2[1:2])
                expr[0][1][0].kind = c12r
                node = SyntaxTree(
                    node.kind,  expr[0], transformed_by="n_" + node.kind
                    )
            pass
        return node


    def n_call_exprn_4_name_expr_0(self, call_node):
        expr = call_node[0]
        if expr[0] == 'name_expr':
            fn_name = expr[0][0]
        else:
            assert expr[0] == 'VARREF'
            fn_name = expr[0]

        if ( fn_name == 'CONSTANT' and
             fn_name.attr in frozenset(['global-set-key', 'local-set-key']) ):
            key_expr = call_node[1][0]
            if  key_expr == 'name_expr' and key_expr[0] == 'CONSTANT':
                emacs_key_normalize(key_expr)
                pass
            pass
        return node

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
        return node

    def traverse(self, node):
        self.preorder(node)

    def transform(self, ast):
        # self.maybe_show_tree(ast)
        self.ast = copy(ast)
        self.ast = self.traverse(self.ast, is_lambda=False)
        return self.ast


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

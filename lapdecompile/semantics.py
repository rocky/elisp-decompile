# -*- coding: utf-8 -*-
"""
Syntax-directed translation from (transformed) parse tree to Elisp source code.
"""

# The below is a bit long, but still it is somehwat abbreviated.
# See https://github.com/rocky/python-uncompyle6/wiki/Table-driven-semantic-actions.
# for a more complete explanation, nicely marked up and with examples.
#
# Semantic action rules for nonterminal symbols can be specified here by
# creating a method prefaced with "n_" for that nonterminal. For
# example, "n_exec_stmt" handles the semantic actions for the
# "exec_stmt" nonterminal symbol. Similarly if a method with the name
# of the nonterminal is suffixed with "_exit" it will be called after
# all of its children are called.
#
# After a while writing methods this way, you'll find many routines which do similar
# sorts of things, and soon you'll find you want a short notation to
# describe rules and not have to create methods at all.
#
# So another other way to specify a semantic rule for a nonterminal is
# via the table MAP_DIRECT where the key is the nonterminal name.
#
# These dictionaries use a printf-like syntax to direct substitution
# from attributes of the nonterminal and its children..
#
# The rest of the below describes how table-driven semantic actions work
# and gives a list of the format specifiers. The default() and
# template_engine() methods implement most of the below.
#
# We allow for a couple of ways to interact with a node in a tree.  So
# step 1 after not seeing a custom method for a nonterminal is to
# determine from what point of view tree-wise the rule is applied.

# In the diagram below, N is a nonterminal name, and K also a nonterminal
# name but the one used as a key in the table.
# we show where those are with respect to each other in the
# AST tree for N.
#
#
#           N&K
#         /  | ... \
#        O   O      O
#
#      TABLE_DIRECT
#
#   The key K is then extracted from the subtree and used to find one
#   of the tables, T listed above.  The result after applying T[K] is
#   a format string and arguments (a la printf()) for the formatting
#   engine.
#
#   Escapes in the format string are:
#
#     %c  evaluate the node recursively. Its argument is a single
#         integer or tuple representing a node index.
#         If a tuple is given, the first item is the node index while
#         the second item is a string giving the node/noterminal name.
#         This name will be checked at runtime against the node type.
#
#     %C  evaluate indicated children in order each on a new line.
#         Its argument is a tuple of start and end node indices.
#
#     %Q  like %c but assumes the first argument has already been quoted.
#         Used in things like (setq x ...) where x might be a variable ref
#         which shouldn't be quoted. Calls are simlar too.
#
#     %L  takes a tuple of node indices: low and high. Evaluates
#         nodes low to high inserting a space in between each one.
#
#     %l  like %L but skips the last node in the list which is
#         presumed to be an operator
#
#     %p  pushes a value of the eval stack to use as an argument.
#         Its argument is like %c.
#     %P  pops a value of the eval stack to use as an argument.
#         effectively discards the value that is on the stack.
#
#     %S  like %P but we use or write the value of the stack.
#         The stack value can either be an AST node or a string.
#         If a node, the we preorder the node to add the string value
#         If a string, then we just use that. Note this brings out
#         the symbolic nature of our eval stack. We are not saving
#         value, but symbolic names of variables and so on.
#
#     %|  Insert spaces to the current indentation level. Takes no arguments.
#
#     %. Set the indent level to be where we currently are at[d. Takes no arguments.

#     %+ increase current indentation level. Takes no arguments.
#        pushes indent level on onto stack. Note that %)
#        decreases the indent.
#
#     %- decrease current indentation level. Takes no arguments.
#        indent level is obtained from the stack Note that %)
#        decreases the indent, so often this isn't needed.
#
#     %_ decrease current indentation level of an if statement for an else
#        block. It is expected that there will be another %_ after the else.
#        Takes no arguments.
#
#     %) decrease current indentation level and writes ')'. Takes no arguments.
#        indent level is obtained from the stack
#
#     %{...} evaluate ... in context of N
#
#     %% literal '%'. Takes no arguments.
#
#
#   The '%' may optionally be followed by a number (C) in square
#   brackets, which makes the template_engine walk down to N[C] before
#   evaluating the escape code.

from __future__ import print_function

import re
from spark_parser import GenericASTTraversal, GenericASTTraversalPruningException
from lapdecompile.scanner import Func
from lapdecompile.tok import Token
from lapdecompile.semantic_consts import TAB, TABLE_DIRECT

from io import StringIO

escape = re.compile(
    r"""
            (?P<prefix> [^%]* )
            % ( \[ (?P<child> -? \d+ ) \] )?
                ((?P<type> [^{] ) |
                 ( [{] (?P<expr> [^}]* ) [}] ))
        """,
    re.VERBOSE,
)


class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg


class SourceWalker(GenericASTTraversal, object):

    indent = property(
        lambda s: s.params["indent"],
        lambda s, x: s.params.__setitem__("indent", x),
        lambda s: s.params.__delitem__("indent"),
        None,
    )

    def __init__(self, ast, debug=False):
        GenericASTTraversal.__init__(self, ast=None)
        params = {"f": StringIO(), "indent": ""}
        self.params = params
        self.param_stack = []
        self.debug = debug
        self.ERROR = None
        self.pending_newlines = 0
        self.indent_stack = [""]

        # A place to put the AST nodes for compuations pushed
        # on the evaluation stack
        self.eval_stack = []

        # By default symbols will be quoted. Rules like setq and
        # call change this and set True temporarily.
        self.noquote = False
        return

    f = property(
        lambda s: s.params["f"],
        lambda s, x: s.params.__setitem__("f", x),
        lambda s: s.params.__delitem__("f"),
        None,
    )

    def pop1(self):
        return self.eval_stack.pop()

    def push1(self, node):
        self.eval_stack.append(node)
        return node

    def access(self):
        return self.eval_stack[0]

    def stacklen(self):
        return len(self.eval_stack)

    def replace1(self, node):
        """Replace the stack top with node.
        Unary ops do this for example"""
        if self.stacklen():
            self.eval_stack[-1] = node

    # def binary_op(self, node):
    #     """Pop 2 items from stack push the result.
    #     binary ops do this for example"""
    #     self.pop1()
    #     self.replace1(node)

    def indent_more(self, indent=TAB):
        self.indent += indent
        if self.debug:
            print("XXX indent more len %d" % len(self.indent))
        self.indent_stack.append(self.indent)

    def indent_less(self, indent=None):
        if indent is None:
            self.indent_stack.pop()
            self.indent = self.indent_stack[-1]
        else:
            self.indent_stack[-1] = self.indent
            self.indent = self.indent[: -len(indent)]
        if self.debug:
            print("XXX indent less len %d" % len(self.indent))

    def find_first_token(self, node):
        if isinstance(node, Token):
            return node
        else:
            return self.find_first_token(node[0])

    def traverse(self, node, indent=None):
        self.param_stack.append(self.params)
        if indent is None:
            indent = self.indent
        else:
            self.indent_stack.append(indent)
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {"f": StringIO(), "indent": indent}
        self.preorder(node)
        self.f.write(u"\n" * self.pending_newlines)
        result = self.f.getvalue()
        self.params = self.param_stack.pop()
        self.pending_newlines = p
        return result

    def n_dolist_init_var(self, node):
        self.write(node[0][-1].attr)
        self.prune()

    def n_dolist_macro(self, node):
        assert node[0] == "dolist_list"
        dolist_init_var = node[1]
        assert dolist_init_var == "dolist_init_var"
        self.push1(self.traverse(dolist_init_var[0][1]))
        try:
            self.template_engine(("%(dolist%+%(%c %c)\n%|", 1, 0), node)
        except GenericASTTraversalPruningException:
            pass
        assert node[6] in ("body", "body_stacked")
        body = node[6]
        skipped_last = False
        if body[0] == "exprs" and body[0][0] == "expr_stmt":
            # If we have a list of exprs and the last one is about --dolist-tail--
            # it is part of the iteration, so skip it.
            exprs = body[0]
            last_expr_stmt = exprs[-1]
            token = self.find_first_token(last_expr_stmt)
            if token == "VARREF" and token.attr == "--dolist-tail--":
                for n in exprs[:-1]:
                    self.preorder(n)
                skipped_last = True
        if not skipped_last:
            self.preorder(body)
        try:
            self.template_engine(("%)",), node)
        except GenericASTTraversalPruningException:
            pass
        self.prune()

    def n_discard(self, node):
        self.pop1()

    def n_unary_expr_stacked(self, node):
        assert 1 <= len(node) <= 2
        if node[0] == "expr_stacked":
            self.template_engine(TABLE_DIRECT["unary_expr"], node)
        elif node[0] == "unary_op":
            self.template_engine(("(%c %S)", 0), node[0])
        else:
            self.template_engine(TABLE_DIRECT["unary_expr_stacked"], node)
        self.prune()

    def n_unwind_protect_form(self, node):
        expr = node[0]
        opt_exprs = node[2]
        assert expr == "expr"
        assert opt_exprs == "opt_exprs"
        self.template_engine(("%(unwind-protect\n%+%|%c", 0), node)
        for e in opt_exprs:
            self.template_engine(("\n%|%Q", 0), e)
        self.template_engine(")", node)
        self.prune()

    def n_varlist_stacked(self, node):
        assert len(node) == 4
        self.template_engine(("(%c %c)", -1, 0), node)
        self.push1(node[0])
        assert node[1] == "varlist_stacked_inner"
        self.n_varlist_stacked_inner(node[1])
        self.prune()

    def n_CONSTANT(self, node):
        if isinstance(node.attr, Func):
            self.f.write(node.attr.name)
            return
        elif not (
            re.match(r"^[0-9]+$", node.attr)
            or node.attr.startswith('"')
            or node.attr in ("t", "nil")
            or self.noquote
        ):
            # Not integer or string and not explicitly unquoted
            self.f.write(u"'")
        self.f.write(node.attr)

    def n_varlist_stacked_inner(self, node):
        if len(node) == 3:
            self.template_engine(("%(%c %c)", -1, 0), node)
        elif len(node) == 1:
            self.template_engine(("\n(%c)", 0), node)
        else:
            assert len(node) == 0

    def n_clause(self, node):
        l = len(node)

        start_stacklen = self.stacklen()
        assert l == 2 or l == 3
        if l == 2:
            self.template_engine(("\n%|(t %.%c", 0), node)
        # Check for first item in a (cond ..)
        elif node[0] == "opt_label" and node[2][-1] != "COME_FROM":
            self.template_engine(("\n%|(t %+%c", 1), node)
            first_clause = False
        else:
            self.template_engine(("\n%|(%c %+%c", 0, 1), node)
            first_clause = True
        if self.stacklen() > start_stacklen:
            if self.access().kind != "VARSET":
                self.write("%s" % self.access())
            self.pop1()
            if first_clause:
                self.template_engine(("%-",), node)

        assert start_stacklen == self.stacklen()
        self.write(")")
        self.indent_less()
        self.prune()

    def n_varbind(self, node):
        if len(node) == 3:
            self.template_engine(("(%c %c)%c", 1, 0, 2), node)
        else:
            self.template_engine(("%(%c %c)", 1, 0), node)
        self.prune()

    def n_call_exprn(self, node):
        if node[-1] == "CALL_0":
            self.template_engine(("(%Q)", 0), node)
        else:
            args = node[-1].attr
            self.template_engine(("(%p%Q %l%P)", 0, 0, (1, args + 1)), node)
        self.prune()

    def n_let_form_star(self, node):
        if node[0] == "varlist" and len(node[0]) == 1:
            # If we have just one binding, use let rather than let*.
            # Also don't put the varbind on a new line as we would
            # do if there were more than one.
            self.template_engine(("%(let %+(%.",), node)
            varbind = node[0][0]
            assert varbind == "varbind"
            self.template_engine(("(%c %c)%)", -1, 0), varbind)
            self.template_engine(("\n%|%c%)", -1), node)
        else:
            self.template_engine(("%(let* %.(%.%c)\n%|%c%)", 0, 1), node)
        self.prune()

    # def n_binary_expr(self, node):
    #     self.binary_op(node)
    #     self.template_engine(( '(%c %c %c)', 2, 0, 1), node)

    def n_unary_expr(self, node):
        self.template_engine(("(%c %c)", 1, 0), node)
        self.replace1(node)
        self.prune()

    def n_expr_stmt(self, node):
        if len(node) == 1:
            self.template_engine(("%c", 0), node)
        elif len(node) == 2 and node[1] == "opt_discard":
            if node[0] == "expr" and node[0][0] == "name_expr":
                value = self.traverse(node[0][0])
                self.push1(value)
                self.write(value)
            else:
                self.template_engine(("%c", 0), node)
        else:
            self.template_engine(("%C", (0, 1000)), node)
        self.prune()

    def n_opt_discard(self, node):
        if len(node) == 1:
            assert node[0] == "DISCARD"
            self.pop1()
        self.prune()

    def n_or_form(self, node):
        if node[1] == "GOTO-IF-NOT-NIL-ELSE-POP":
            self.template_engine(("(or %+%c%p %c%)", 0, 0, 2), node)
        else:
            self.template_engine(("(or %+%c %c%)", 0, 2), node)
        self.prune()

    def n_progn(self, node):
        assert node[0] == "body"
        exprs = node[0][0]
        if len(exprs) == 1:
            self.template_engine(("%c", 0), exprs)
        else:
            self.template_engine(("%(progn\n%+%|%c%)", 0), node)
        self.prune()

    def n_DUP(self, node):
        if self.stacklen() == 0:
            self.write("DUP-empty-stack")
        else:
            val = self.eval_stack[0]
            s = val if isinstance(val, str) else self.traverse(val)
            self.write(s)

    def n_with_current_buffer_safe_macro(self, node):
        self.template_engine(
            ("%(with-current-buffer-safe %c\n%+%|%D%)", (1, "VARREF"), (4, 1000)),
            node[11],
        )
        self.prune()

    def template_engine(self, entry, startnode):
        """The format template engine.  See the comment at the beginning of
        this module for the how we interpret format specifications
        such as %c, %C, %l and so on and what arguments they expect.
        """

        # self.println("-----")
        if self.debug:
            print("XXX", startnode.kind)

        fmt = entry[0]
        arg = 1
        i = 0

        m = escape.search(fmt)
        while m:
            i = m.end()
            self.write(m.group("prefix"))

            typ = m.group("type") or "{"
            node = startnode
            try:
                if m.group("child"):
                    node = node[int(m.group("child"))]
            except:
                print(node.__dict__)
                raise

            if typ == "%":
                self.write("%")
            elif typ == ".":
                count = len(self.f.getvalue().split("\n")[-1]) - len(self.indent)
                if self.debug:
                    print("XXX . indent count", count)
                self.indent_more(" " * count)
            elif typ == "+":
                self.indent_more()
            elif typ == "-":
                self.indent_less()

            elif typ == "_":
                self.indent_less("  ")  # For else part of if/else
            elif typ == "|":
                self.write(self.indent)
            elif typ == ")":
                self.write(")")
                self.indent_less()
            elif typ == "c":
                index = entry[arg]
                if isinstance(index, tuple):
                    assert node[index[0]] == index[1], (
                        "at %s[%d], expected %s node; got %s"
                        % (node.kind, arg, index[1], node[index[0]].kind)
                    )
                    index = index[0]
                assert isinstance(
                    index, int
                ), "at %s[%d], %s should be int or tuple" % (
                    node.kind,
                    arg,
                    type(index),
                )
                self.preorder(node[index])
                arg += 1
            elif typ == "Q":
                # Like 'c' but no quoting
                self.noquote = True
                index = entry[arg]
                if isinstance(index, tuple):
                    assert node[index[0]] == index[1], (
                        "at %s[%d], expected %s node; got %s"
                        % (node.kind, arg, node[index[0]].kind, index[1])
                    )
                    index = index[0]
                assert isinstance(
                    index, int
                ), "at %s[%d], %s should be int or tuple" % (
                    node.kind,
                    arg,
                    type(index),
                )
                self.preorder(node[index])
                self.noquote = False
                arg += 1
            elif typ == "S":
                # Get value from eval stack
                subnode = self.pop1()
                if isinstance(subnode, str):
                    self.write(subnode)
                else:
                    self.preorder(subnode)
            elif typ == "p":
                # Push value to eval stack
                index = entry[arg]
                self.push1(node[index])
                arg += 1
            elif typ == "P":
                self.pop1()
                arg += 1
            elif typ == "l":
                low, high = entry[arg]
                remaining = len(node[low:high]) - 1
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining >= 0:
                        self.write(" ")
                        pass
                    pass
                arg += 1
            elif typ == "L":
                low, high = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(" ")
                        pass
                    pass
                arg += 1
            elif typ == "C":
                low, high = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write("\n" + self.indent)
                        pass
                    pass
                arg += 1
            elif typ == "D":
                # See if we can parameterize "C" better to DRY this
                low, high = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 1:  # %C we use 0
                        self.write("\n" + self.indent)
                        pass
                    pass
                arg += 1
            elif typ == "{":
                d = node.__dict__
                expr = m.group("expr")
                try:
                    self.write(eval(expr, d, d))
                except:
                    print(node)
                    raise
            elif typ == "(":
                if not self.f.getvalue().endswith("\n" + self.indent):
                    self.write("\n" + self.indent)
                self.write("(")
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        key = node

        if key.kind in TABLE_DIRECT:
            self.template_engine(TABLE_DIRECT[key.kind], node)
            self.prune()

    def write(self, *data):
        udata = [d for d in data]
        self.f.write(*udata)
        return

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
# So another other way to specify a semantic rule for a nonterminal is via
# one of the tables MAP_R0, MAP_R, or MAP_DIRECT where the key is the
# nonterminal name.
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
#          N&K               N                  N
#         / | ... \        / | ... \          / | ... \
#        O  O      O      O  O      K         O O      O
#                                                      |
#                                                      K
#      TABLE_DIRECT      TABLE_R             TABLE_R0
#
#   The default table is TABLE_DIRECT. By far, most rules used work this way.
#   TABLE_R0 is rarely used.

#   The key K is then extracted from the subtree and used to find one
#   of the tables, T listed above.  The result after applying T[K] is
#   a format string and arguments (a la printf()) for the formatting
#   engine.
#
#   Escapes in the format string are:
#
#     %c  evaluate the node recursively. Its argument is a single
#         integer representing a node index.
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
#     %s  pushes a value of the eval stack to use as an argument.
#         _stacked nonterminals work this way
#     %S  pops a value of the eval stack to use as an argument.
#         _stacked nonterminals work this way
#
#     %|  Insert spaces to the current indentation level. Takes no arguments.
#
#     %. Set the indent level to be where we currently are at[d. Takes no arguments.

#     %+ increase current indentation level. Takes no arguments.
#        pushes indent level on onto stack
#
#     %- decrease current indentation level. Takes no arguments.
#        indent level is obtained from the stack
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

import re, sys
from spark_parser import GenericASTTraversal, GenericASTTraversalPruningException
from eldecompile.tok import Token

try:
    from io import StringIO
except:
    from StringIO import StringIO

PYTHON3 = (sys.version_info >= (3, 0))


TAB = ' ' *4   # is less spacy than "\t"
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level
TABLE_R = {
}

TABLE_R0 = {
}

TABLE_DIRECT = {
    'setq_expr':	   ( '%(setq %Q %+%c%)', -1,
                             (0, "expr") ),
    'setq_expr_stacked':   ( '%(setq %Q %+%c%)', -1, 0 ),
    'set_expr':            ( '%(set %c %+%c%)',
                             (0, "expr"), (1, "expr") ),
    'nullary_expr':	   ( '(%c)', 0 ),
    'unary_expr':	   ( '(%c %+%c%)', 1, 0 ),
    'unary_expr_stacked':  ( '(%c %+%S%)', 0 ),
    'binary_expr':	   ( '(%c %+%c %c%)',
                             (-1, "binary_op"),
                             (0, "expr"), (1, "expr") ),
    'binary_expr_stacked': ( '(%c %+%S %c%)', -1, 0),

    'concat_exprn':	   ( '(concat %l)', (0, 1000) ),
    'list_exprn':	   ( '(list %l)', (0, 1000) ),
    'min_exprn':	   ( '(min %L)', (0, 1000) ),
    'max_exprn':	   ( '(max %L)', (0, 1000) ),
    'save_excursion':      ( '(save-excursion\n%+%|%c%)',
                             (1, "body") ),
    'save_current_buffer': ( '(save-current-buffer\n%+%|%c%)',
                             (1, "body") ),
    'set_buffer':          ( '(set-buffer %c)',
                             (0, "expr") ),

    'cond_expr':	   ( '%(cond %.%c%c%)', 0, 1 ),
    'labeled_clause':	   ( '%c', 1 ),
    'labeled_final_clause': ('\n%|(%c %c)', 1, 2),

    'if_expr':		  ( '%(if %c\n%+%|%c%)', 0, 2 ),
    'if_else_expr':	  ( '%(if %c\n%+%|%c%_%c)%_', 0, 2, 5 ),
    'while_expr':	  ( '%(while %c\n%+%|%c%)', 2, 4 ),
    'while_expr_stacked':	( '%(while %s%c\n%+%|%c%)', 0, 3, 5 ),
    'when_expr':	  ( '%(when %c\n%+%|%c%)', 0, 2 ),
    'or_expr':		  ( '(or %+%c %c%)', 0, 2 ),
    'and_expr':		  ( '(and %+%c %c%)', 0, 2 ),
    'not_expr':		  ( '(null %+%c%)', 0 ),
    'dolist_expr_result': ( '%(dolist%+%(%c %c %c)\n%_%|%c)%_', 1, 0, 16, 6),

    'pop_expr':           ( '(pop %+%c%)', (0, 'VARREF')),

    'exprs':              ( '%C', (0, 1000) ),


    'let_expr_stacked':	( '%(let %.(%.%c)%-%c%)', 0, 1 ),
    # 'progn':		( '%(progn\n%+%|%c%)', 0 ),
    'body_stacked':	( '%c', 0 ),

    'ADD1':	( '1+' , ),
    'CAR':	( 'car' , ),
    'CAR-SAFE':	( 'car-safe' , ),
    'DIFF':	( '-' ,  ),
    'EQLSIGN':	( '=' ,  ),
    'NEQLSIGN':	( '/=' , ),  # Can only occur via transform
    'GEQ':	( '>=' , ),
    'GTR':	( '>' ,  ),
    'LEQ':	( '<=' , ),
    'LSS':	( '<' ,  ),
    'MULT':	( '*' ,  ),
    'PLUS':	( '+' ,  ),
    'QUO':	( '/' ,  ),
    'REM':	( '%' ,  ),
    'SUB1':	( '1-' , ),

    'TSTRING':	        ( '%{attr}', ),
    'VARSET':	        ( '%{attr}', ),
    'VARBIND':	        ( '%{attr}', ),
    'VARREF':	        ( '%{attr}', ),
    'STACK-REF':	( 'stack-ref%{attr}', ),
}

NULLARY_OPS = tuple("""
point
point-min
point-max
following-char
preceding-char
current-column
eolp
bolp
current-buffer
widen
""".split())

UNARY_OPS = tuple("""
car cdr cdr-safe consp
insert integerp
keywordp listp
markerp mutexp
multibyte-string-p
natnump
nlistp
not
null numberp
recordp
sequencep stringp subr-arity subrp
symbol-function symbol-plist symbol-name symbolp
threadp
type-of
user-ptrp
vector-or-char-tablep vectorp
""".split())

BINARY_OPS = tuple("""
aref eq equal fset max min
remove-variable-watcher
setcar setcdr setplist
""".split())

for op in BINARY_OPS + UNARY_OPS + NULLARY_OPS:
    TABLE_DIRECT[op.upper()] = ( op, )


MAP_DIRECT = (TABLE_DIRECT, )

escape = re.compile(r'''
            (?P<prefix> [^%]* )
            % ( \[ (?P<child> -? \d+ ) \] )?
                ((?P<type> [^{] ) |
                 ( [{] (?P<expr> [^}]* ) [}] ))
        ''', re.VERBOSE)

def to_s(s):
    if PYTHON3:
        return s
    else:
        return s.decode('utf-8')

class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg

class SourceWalker(GenericASTTraversal, object):

    indent = property(lambda s: s.params['indent'],
                 lambda s, x: s.params.__setitem__('indent', x),
                 lambda s: s.params.__delitem__('indent'),
                 None)

    def __init__(self, ast, debug=False):
        GenericASTTraversal.__init__(self, ast=None)
        params = {
            'f': StringIO(),
            'indent': '',
            }
        self.params = params
        self.param_stack = []
        self.debug = debug
        self.ERROR = None
        self.prec = 100
        self.pending_newlines = 0
        self.indent_stack = ['']

        # A place to put the AST nodes for compuations pushed
        # on the evaluation stack
        self.eval_stack = []

        # By default symbols will be quoted. Rules like setq and
        # call change this and set True temporarily.
        self.noquote = False
        return

    f = property(lambda s: s.params['f'],
                 lambda s, x: s.params.__setitem__('f', x),
                 lambda s: s.params.__delitem__('f'),
                 None)

    def pop1(self):
        return self.eval_stack.pop()

    def push1(self, node):
        self.eval_stack.append(node)
        return node

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
            self.indent = self.indent[:-len(indent)]
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
        self.params = {
            'f': StringIO(),
            'indent': indent,
            }
        self.preorder(node)
        self.f.write(u'\n'*self.pending_newlines)
        result = self.f.getvalue()
        self.params = self.param_stack.pop()
        self.pending_newlines = p
        return result

    def n_dolist_init_var(self, node):
        self.write(node[0][-1].attr)
        self.prune()

    def n_dolist_expr(self, node):
        assert node[0] == 'dolist_list'
        assert node[1] == 'dolist_init_var'
        try:
            self.template_engine(("%(dolist%+%(%c %c)\n%_%|", 1, 0), node)
        except GenericASTTraversalPruningException:
            pass
        assert node[6] == 'body'
        body = node[6]
        skipped_last = False
        if body[0] == 'exprs' and body[0][0] == 'expr_stmt':
            # If we have a list of exprs and the last one is about --dolist-tail--
            # it is part of the iteration, so skip it.
            exprs = body[0]
            last_expr_stmt = exprs[-1]
            token = self.find_first_token(last_expr_stmt)
            if token == 'VARREF' and token.attr == '--dolist-tail--':
                for n in exprs[:-1]:
                    self.preorder(n)
                skipped_last = True
        if not skipped_last:
            self.preorder(body)
        try:
            self.template_engine(")%_", node)
        except GenericASTTraversalPruningException:
            pass
        self.prune()

    def n_discard(self, node):
        self.pop1()

    def n_unary_expr_stacked(self, node):
        assert len(node) == 2
        if node[0] == 'expr_stacked':
            self.template_engine(TABLE_DIRECT['unary_expr'], node)
        else:
            self.template_engine(TABLE_DIRECT['unary_expr_stacked'], node)
        self.prune()

    def n_varlist_stacked(self, node):
        assert len(node) == 4
        self.template_engine(( '(%c %c)', -1, 0 ), node)
        self.push1(node[0])
        assert node[1] == 'varlist_stacked_inner'
        self.n_varlist_stacked_inner(node[1])
        self.prune()

    def n_CONSTANT(self, node):
        if (not (re.match(r'^[0-9]+$', node.attr)
                 or node.attr.startswith('"')
                 or node.attr in ('t', 'nil')
                 or self.noquote)):
            # Not integer or string and not explicitly unquoted
            self.f.write(u"'")
        self.f.write(to_s(node.attr))

    def n_varlist_stacked_inner(self, node):
        if len(node) == 3:
            self.template_engine( ('%(%c %c)', -1, 0 ), node)
        elif len(node) == 1:
            self.template_engine( ('\n(%c)', 0 ), node)
        else:
            assert len(node) == 0

    def n_clause(self, node):
        l = len(node)

        start_stacklen = self.stacklen()
        assert l == 2 or l == 3
        if l == 2:
            self.template_engine( ('\n%|(t %.%c', 0), node)
        elif node[0] == 'opt_label':
            self.template_engine( ('\n%|(t %.%c', 1), node)
        else:
            self.template_engine( ('\n%|(%c %.%c', 0, 1), node)
        if self.stacklen() > start_stacklen:
            self.write("%s" % self.pop1())

        assert start_stacklen == self.stacklen()
        self.write(')')
        self.indent_less()
        self.prune()

    def n_varbind(self, node):
        if len(node) == 3:
            self.template_engine( ('(%c %c)%c', 1, 0, 2), node)
        else:
            self.template_engine( ('%(%c %c)', 1, 0), node)
        self.prune()

    def n_call_exprn(self, node):
        if node[-1] == 'CALL_1':
            self.template_engine( ('(%Q)', 0), node )
        else:
            args = node[-1].attr
            self.template_engine( ('(%Q %l)', 0, (1, args)), node )
        self.prune()

    def n_let_expr_star(self, node):
        if node[0] == 'varlist' and len(node[0]) == 1:
            # If we have just one binding, use let rather than let*.
            # Also don't put the varbind on a new line as we would
            # do if there were more than one.
            self.template_engine( ('%(let %.(%.', ), node )
            varbind = node[0][0]
            assert varbind == 'varbind'
            self.template_engine( ('(%c %c)', 1, 0), varbind)
            self.template_engine( ('%-%c%)', 1 ), node )
        else:
            self.template_engine( ('%(let* %.(%.%c)%-\n%|%c%)%-', 0, 1 ),
                                  node )
        self.prune()

    # def n_binary_expr(self, node):
    #     self.binary_op(node)
    #     self.template_engine(( '(%c %c %c)', 2, 0, 1), node)

    def n_unary_expr(self, node):
        self.replace1(node)
        self.template_engine( ('(%c %c)', 1, 0), node )
        self.prune()

    def n_expr_stmt(self, node):
        if len(node) == 1:
            self.template_engine( ('%c', 0), node )
        elif len(node) == 2 and node[1] == 'opt_discard':
            if node[0] == 'expr' and node[0][0] == 'name_expr':
                value = self.traverse(node[0][0])
                self.push1(value)
            else:
                self.template_engine( ('%c', 0), node )
        else:
            self.template_engine( ('%C', (0, 1000)), node )
        self.prune()

    def n_opt_discard(self, node):
        if len(node) == 1:
            assert node[0] == 'DISCARD'
            self.pop1()
        self.prune()

    def n_progn(self, node):
        assert node[0] == 'body'
        exprs = node[0][0]
        if len(exprs) == 1:
            self.template_engine( ('%c', 0), exprs )
        else:
            self.template_engine( ( '%(progn\n%+%|%c%)', 0 ), node)
        self.prune()

    def n_DUP(self, node):
        if self.stacklen() == 0:
            self.write("DUP-empty-stack")
        else:
            self.write(self.pop1())

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
            self.write(m.group('prefix'))

            typ = m.group('type') or '{'
            node = startnode
            try:
                if m.group('child'):
                    node = node[int(m.group('child'))]
            except:
                print(node.__dict__)
                raise

            if   typ == '%':	self.write('%')
            elif typ == '.':
                count = len(self.f.getvalue().split("\n")[-1]) - len(self.indent)
                if self.debug:
                    print("XXX . indent count", count)
                self.indent_more(' ' * count)
            elif typ == '+':	self.indent_more()
            elif typ == '-':	self.indent_less()
            elif typ == '_':	self.indent_less('  ')  # For else part of if/else
            elif typ == '|':	self.write(self.indent)
            elif typ == ')':
                self.write(')')
                self.indent_less()
            elif typ == "c":
                index = entry[arg]
                if isinstance(index, tuple):
                    assert node[index[0]] == index[1], (
                        "at %s[%d], expected %s node; got %s" % (
                            node.kind, arg, node[index[0]].kind, index[1])
                    )
                    index = index[0]
                assert isinstance(index, int), (
                    "at %s[%d], %s should be int or tuple" % (
                        node.kind, arg, type(index)))
                self.preorder(node[index])
                arg += 1
            elif typ == 'Q':
                # Like 'c' but no quoting
                self.noquote = True
                self.preorder(node[entry[arg]])
                self.noquote = False
                arg += 1
            elif typ == 's':
                # push a value on the eval stack
                self.push1(node[entry[arg]])
                arg += 1
            elif typ == 'S':
                # Get value from eval stack
                subnode = self.pop1()
                self.preorder(subnode)
            elif typ == "p":
                p = self.prec
                tup = entry[arg]
                assert isinstance(tup, tuple)
                if len(tup) == 3:
                    (index, nonterm_name, self.prec) = tup
                    assert node[index] == nonterm_name, (
                        "at %s[%d], expected '%s' node; got '%s'"
                        % (node.kind, arg, nonterm_name, node[index].kind)
                    )
                else:
                    assert len(tup) == 2
                    (index, self.prec) = entry[arg]

                self.preorder(node[index])
                self.prec = p
                arg += 1
            elif typ == 'l':
                low, high = entry[arg]
                remaining = len(node[low:high]) - 1
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining >= 1:
                        self.write(" ")
                        pass
                    pass
                arg += 1
            elif typ == 'L':
                low, high = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining >= 1:
                        self.write(" ")
                        pass
                    pass
                arg += 1
            elif typ == 'C':
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
            elif typ == '{':
                d = node.__dict__
                expr = m.group('expr')
                try:
                    self.write(eval(expr, d, d))
                except:
                    print(node)
                    raise
            elif typ == '(':
                if not self.f.getvalue().endswith("\n" + self.indent):
                    self.write("\n" + self.indent)
                self.write('(')
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        table = MAP_DIRECT[0]
        key = node

        for i in MAP_DIRECT[1:]:
            key = key[i]

        if key.kind in table:
            self.template_engine(table[key.kind], node)
            self.prune()

    def write(self, *data):
        udata = [to_s(d) for d in data]
        try:
            self.f.write(*udata)
        except:
            from trepan.api import debug; debug()
            pass
        return

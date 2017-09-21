# The below is a bit long, but still it is somehwat abbreviated.
# See https://github.com/rocky/python-uncompyle6/wiki/Table-driven-semantic-actions.
# for a more complete explanation, nicely marked up and with examples.
#
#
# Semantic action rules for nonterminal symbols can be specified here by
# creating a method prefaced with "n_" for that nonterminal. For
# example, "n_exec_stmt" handles the semantic actions for the
# "exec_stmt" nonterminal symbol. Similarly if a method with the name
# of the nonterminal is suffixed with "_exit" it will be called after
# all of its children are called.
#
# However if this were done for all of the rules, this file would be even longer
# than it is already.
#
# Another more compact way to specify a semantic rule for a nonterminal is via
# rule given in one of the tables MAP_R0, MAP_R, or MAP_DIRECT.
#
# These uses a printf-like syntax to direct substitution from attributes
# of the nonterminal and its children..
#
# The rest of the below describes how table-driven semantic actions work
# and gives a list of the format specifiers. The default() and
# template_engine() methods implement most of the below.
#
#   Step 1 determines a table (T) and a path to a
#   table key (K) from the node type (N) (other nodes are shown as O):
#
#          N&K               N                  N
#         / | ... \        / | ... \          / | ... \
#        O  O      O      O  O      K         O O      O
#                                                      |
#                                                      K
#      TABLE_DIRECT      TABLE_R             TABLE_R0
#
#   The default is a "TABLE_DIRECT" mapping.  The key K is then extracted from the
#   subtree and used to find a table entry T[K], if any.  The result is a
#   format string and arguments (a la printf()) for the formatting engine.
#   Escapes in the format string are:
#
#     %c  evaluate the node recursively. Its argument is a single
#         integer representing a node index.
#
#     %Q  like %c but assumes the first argument has already been quoted.
#         Used in things like (setq x ...) where x might be a variable ref
#         which shouldn't be quoted. Calls are simlar too.
#
#     %l  takes a tuple of node indices: low and high. Evaluates
#         nodes low to high inserting a space in between each one
#
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
from spark_parser import GenericASTTraversal

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
    'setq_expr':	   ( '%(setq %Q %c)', -1, 0 ),
    'setq_expr_stacked':   ( '%(setq %Q %c)', -1, 0 ),
    'nullary_expr':	       ( '(%c)', 0 ),
    'unary_expr':	   ( '(%c %c)', 1, 0 ),
    'unary_expr_stacked':  ( '(%c %S)', 0 ),
    'binary_expr':	   ( '(%c %c %c)', -1, 0, 1 ),
    'binary_expr_stacked': ( '(%c %S %c)', -1, 0),

    'call_exprn':	( '%(%Q %l)', 0, (1, 1000) ),
    'list_exprn':	( '(list %l)', (0, 1000) ),
    'concat_exprn':	( '(concat %l)', (0, 1000) ),

    'if_expr':		( '%(if %c\n%+%|%c%)', 0, 2 ),
    'if_expr':		( '%(if %c\n%+%|%c%)', 0, 2 ),
    'if_else_expr':	( '%(if %c\n%+%|%c%_%c%)%_', 0, 2, 6 ),

    'let_expr_stacked':	( '%(let %.(%.%c)%-%-%c%)', 0, 1 ),
    'let_expr_star':	( '%(let* %.(%.%c)%-%-%c%)', 0, 1 ),
    'progn':		( '%(progn%+%c)', 0 ),
    'body_stacked':	( '%c', 0 ),
    'expr':		( '%C', (0, 10000) ),
    'expr_stacked':	( '%C', (0, 10000) ),

    'ADD1':	( '1+' , ),
    'DIFF':	( '-' ,  ),
    'EQLSIGN':	( '=' ,  ),
    'GEQ':	( '>=' , ),
    'GTR':	( '>' ,  ),
    'LEQ':	( '<=' , ),
    'LSS':	( '<' ,  ),
    'MULT':	( '*' ,  ),
    'PLUS':	( '+' ,  ),
    'QUO':	( '/' ,  ),
    'REM':	( '%' ,  ),

    'VARSET':	        ( '%{attr}', ),
    'VARBIND':	        ( '%{attr}', ),
    'VARREF':	        ( '%{attr}', ),
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
car cdr cdr-safe
integerp
keywordp listp
markerp mutexp
multibyte-string-p
nlistp
not
null natnump numberp
recordp
sequencep stringp subr-arity subrp symbolp
symbol-function symbol-plist symbol-name
threadp
user-ptrp
vector-or-char-tablep vectorp
type-of
""".split())

BINARY_OPS = tuple("""
aref eq fset max min
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

    def __init__(self, ast, debug=True):
        GenericASTTraversal.__init__(self, ast=None)
        params = {
            'indent': '',
            }
        self.params = params
        self.debug = debug
        self.ERROR = None
        self.pending_newlines = 0
        self.hide_internal = True
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


    def replace1(self, node):
        """Replace the stack top with node.
        Unary ops do this for example"""
        if len(self.eval_stack):
            self.eval_stack[-1] = node

    # def binary_op(self, node):
    #     """Pop 2 items from stack push the result.
    #     binary ops do this for example"""
    #     self.pop1()
    #     self.replace1(node)


    # def n_let_expr(self, node):
    #     from trepan.api import debug; debug()
    #     self.default(node)

    def n_discard(self, node):
        self.pop1()

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

    def indent_more(self, indent=TAB):
        self.indent += indent
        if self.debug:
            print("XXX indent more len %d" % len(self.indent))
        self.indent_stack.append(self.indent)

    def indent_less(self, indent=None):
        if indent is None:
            self.indent = self.indent_stack.pop()
        else:
            self.indent_stack[-1] = self.indent
            self.indent = self.indent[:-len(indent)]
        if self.debug:
            print("XXX indent less len %d" % len(self.indent))

    def traverse(self, node, indent=None, isLambda=False):
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            'f': StringIO(),
            'indent': indent,
            }
        self.preorder(node)
        self.f.write(u'\n'*self.pending_newlines)
        result = self.f.getvalue()
        self.pending_newlines = p
        return result

    def n_varlist_stacked_inner(self, node):
        if len(node) == 3:
            self.template_engine( ('%(%c %c)', -1, 0 ), node)
        elif len(node) == 1:
            self.template_engine( ('\n(%c)', 0 ), node)
        else:
            assert len(node) == 0

    def n_varbind(self, node):
        if len(node) == 3:
            self.template_engine( ('(%c %c)%c', 1, 0, 2), node)
        else:
            self.template_engine( ('%(%c %c)', 1, 0), node)
        self.prune()


    # def n_binary_expr(self, node):
    #     self.binary_op(node)
    #     self.template_engine(( '(%c %c %c)', 2, 0, 1), node)

    def n_unary_expr(self, node):
        self.replace1(node)
        self.template_engine( ('(%c %c)', 1, 0), node )
        self.prune()

    def template_engine(self, entry, startnode):
        """The format template engine.  See the comment at the beginning of
        this module for the how we interpret format specifications
        such as %c, %C, %l and so on and what arguments they expect.
        """

        # self.println("-----")
        # print("XXX", startnode)

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
            elif typ == 'c':
                self.preorder(node[entry[arg]])
                arg += 1
            elif typ == 'Q':
                # Like 'c' but no quoting
                self.noquote = True
                self.preorder(node[entry[arg]])
                self.noquote = False
                arg += 1
            elif typ == 'S':
                # Get value from eval stack
                subnode = self.pop1()
                self.preorder(subnode)
            elif typ == 'p':
                (index, self.prec) = entry[arg]
                self.preorder(node[index])
            elif typ == 'l':
                low, high = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 1:
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
            elif typ == ')':
                self.write(')')
                self.indent_less()
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        table = MAP_DIRECT[0]
        key = node

        for i in MAP_DIRECT[1:]:
            key = key[i]

        if key.type in table:
            self.template_engine(table[key.type], node)
            self.prune()

    def write(self, *data):
        udata = [to_s(d) for d in data]
        self.f.write(*udata)
        return

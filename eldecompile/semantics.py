import re
from spark_parser import GenericASTTraversal

try:
    from io import StringIO
except:
    from StringIO import StringIO


TAB = ' ' *4   # is less spacy than "\t"
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level
TABLE_R = {
}

TABLE_R0 = {
}

TABLE_DIRECT = {
    'setq_expr':	( '%(setq %Q %c)', -1, 0),
    'binary_expr':	( '(%c %c %c)', 2, 0, 1),
    'unary_expr':	( '(%c %c)', 1, 0),

    'call_expr0':	( '(%Q)', 0),
    'call_expr1':	( '(%Q %c)', 0, 1),
    'call_expr2':	( '(%Q %c %c)', 0, 1, 2),
    'call_expr3':	( '(%Q %c %c %c)', 0, 1, 2, 3),

    'if_expr':		( '%(if %c\n%+%|%c%)', 0, 2),
    'progn':		( '%(progn%+%c%c%)', 0, 1),
    'expr':		( '%C', (0, 10000)),

    'ADD1':	( '1+' ,),
    'DIFF':	( '-' ,),
    'EQLSIGN':	( '=' ,),
    'GEQ':	( '>=' ,),
    'GTR':	( '>' ,),
    'LEQ':	( '<=' ,),
    'LSS':	( '<' ,),
    'MULT':	( '*' ,),
    'PLUS':	( '+' ,),
    'QUO':	( '/' ,),
    'REM':	( '%' ,),

    'VARSET':	        ( '%{attr}', ),
    'VARREF':	        ( '%{attr}', ),
}

UNARYOPS = tuple("""
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

BINOPS = tuple("""
aref eq fset max min
remove-variable-watcher
setcar setcdr setplist
""".split())

for op in BINOPS + UNARYOPS:
    TABLE_DIRECT[op.upper()] = ( op, )


MAP_DIRECT = (TABLE_DIRECT, )

escape = re.compile(r'''
            (?P<prefix> [^%]* )
            % ( \[ (?P<child> -? \d+ ) \] )?
                ((?P<type> [^{] ) |
                 ( [{] (?P<expr> [^}]* ) [}] ))
        ''', re.VERBOSE)

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

    def __init__(self, ast):
        GenericASTTraversal.__init__(self, ast=None)
        params = {
            'indent': '',
            }
        self.params = params
        self.ERROR = None
        self.pending_newlines = 0
        self.hide_internal = True

        # By default symbols will be quoted. Rules like setq and
        # call change this and set True temporarily.
        self.noquote = False
        return

    f = property(lambda s: s.params['f'],
                 lambda s, x: s.params.__setitem__('f', x),
                 lambda s: s.params.__delitem__('f'),
                 None)

    def n_CONSTANT(self, node):
        if not (re.match(r'[0-9"]', node.attr[0]) or self.noquote):
            # Not integer or string and not explicitly unquoted
            self.f.write(u"'")
        self.f.write(node.attr.decode('utf-8'))

    def indentMore(self, indent=TAB):
        self.indent += indent

    def indentLess(self, indent=TAB):
        self.indent = self.indent[:-len(indent)]

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


    def engine(self, entry, startnode):
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format specifications such as
        %c, %C, and so on.
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
            elif typ == '+':	self.indentMore()
            elif typ == '-':	self.indentLess()
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
            elif typ == 'p':
                (index, self.prec) = entry[arg]
                self.preorder(node[index])
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
            elif typ == 'P':
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                remaining = len(node[low:high])
                # remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                self.prec = p
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
                self.indentLess()
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        table = MAP_DIRECT[0]
        key = node

        for i in MAP_DIRECT[1:]:
            key = key[i]

        if key.type in table:
            self.engine(table[key.type], node)
            self.prune()

    def write(self, *data):
        udata = [d.decode('utf-8') for d in data]
        self.f.write(*udata)
        return

"""Spark Earley Algorithm parser ELISP
"""

import re
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

nop_func = lambda self, args: None

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, start='fn_exprs', debug=PARSER_DEFAULT_DEBUG):
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(['exprs', 'varlist'])
        self.new_rules = set()

    def nonterminal(self, nt, args):
        if nt in self.collect and len(args) > 1:
            #
            #  Collect iterated thingies together. That is rather than
            #  stmts -> stmts stmt -> stmts stmt -> ...
            #  stmms -> stmt stmt ...
            #
            rv = args[0]
            rv.append(args[1])
        else:
            rv = GenericASTBuilder.nonterminal(self, nt, args)
        return rv

    def p_elisp_grammar(self, args):
        '''
        # The start or goal symbol
        fn_exprs ::= body RETURN

        exprs ::= exprs expr opt_discard
        exprs ::= expr opt_discard
        exprs ::= expr_stacked opt_discard

        progn ::= body

        expr  ::= setq_expr
        expr  ::= binary_expr
        expr  ::= unary_expr
        expr  ::= nullary_expr
        expr  ::= name_expr

        expr  ::= if_expr
        expr  ::= if_else_expr

        body  ::= exprs

        expr_stacked ::= unary_expr_stacked
        expr_stacked ::= setq_expr_stacked

        unary_expr_stacked ::= unary_op
        binary_expr_stacked ::= expr binary_op


        expr  ::= let_expr

        if_expr ::= expr GOTO-IF-NIL-ELSE-POP expr opt_discard LABEL
        if_expr ::= expr GOTO-IF-NIL-ELSE-POP progn opt_discard LABEL
        if_expr ::= expr GOTO-IF-NIL expr opt_discard LABEL
        if_expr ::= expr GOTO-IF-NIL progn opt_discard LABEL

        if_else_expr ::= expr GOTO-IF-NIL expr opt_discard RETURN LABEL expr
        if_else_expr ::= expr GOTO-IF-NIL progn opt_discard RETURN LABEL expr


        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= name_expr expr CALL_1
        call_expr2 ::= name_expr expr expr CALL_2
        call_expr3 ::= name_expr expr expr expr CALL_3

        name_expr ::= CONSTANT
        name_expr ::= VARREF

        binary_expr ::= expr expr bin_op

        bin_op ::= DIFF
        bin_op ::= EQLSIGN
        bin_op ::= GEQ
        bin_op ::= GTR
        bin_op ::= LEQ
        bin_op ::= LSS
        bin_op ::= MULT
        bin_op ::= PLUS
        bin_op ::= QUO
        bin_op ::= REM
        bin_op ::= TIMES

        unary_expr ::= expr unary_op

        unary_op ::= ADD1
        unary_op ::= CAR
        unary_op ::= CDR
        unary_op ::= INTEGERP
        unary_op ::= NOT

        nullary_expr ::= nullary_op

        nullary_op ::= POINT
        nullary_op ::= POINT-MIN
        nullary_op ::= POINT-MAX
        nullary_op ::= FOLLOWING-CHAR
        nullary_op ::= PRECEDING-CHAR
        nullary_op ::= CURRENT-COLUMN
        nullary_op ::= EOLP
        nullary_op ::= BOLP
        nullary_op ::= CURRENT-BUFFER
        nullary_op ::= WIDEN

        setq_expr ::= expr VARSET
        setq_expr ::= expr DUP VARSET
        setq_expr ::= expr DUP VARSET
        setq_expr_stacked ::= expr_stacked DUP VARSET

        let_expr ::= varlist exprs UNBIND

        opt_discard ::= DISCARD?

        varlist  ::= varbind+
        varlist  ::= varbind+
        varbind  ::= expr VARBIND
        varbind  ::= expr DUP VARBIND
        '''
        return

    def add_unique_rule(self, rule, opname):
        """Add rule to grammar, but only if it hasn't been added previously
           opname and count are used in the customize() semantic the actions
           to add the semantic action rule. Often, count is not used.
        """
        if rule not in self.new_rules:
            print("XXX ", rule) # debug
            self.new_rules.add(rule)
            self.addRule(rule, nop_func)
            pass
        return

    def add_custom_rules(self, tokens, customize):
        for opname, v in customize.items():
            if re.match(r'^LIST|CONCAT|CALL', opname):
                opname_base = opname[:opname.index('_')]
                if opname_base[-1] == 'N':
                    opname_base = opname_base[:-1]
                nt = "%s_exprn" % (opname_base.lower())
                rule = '%s ::= %s%s' % (nt, ('expr ' * v), opname)
                self.add_unique_rule(rule, opname_base)
                rule = 'expr  ::= %s' % nt
                self.add_unique_rule(rule, opname_base)
            pass
        return
    pass

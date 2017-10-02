"""Spark Earley Algorithm parser ELISP
"""

import re
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

nop_func = lambda self, args: None

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, start='fn_body', debug=PARSER_DEFAULT_DEBUG):
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(['exprs', 'varlist' 'labeled_clauses'])
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
        '''# The start or goal symbol
        fn_body ::= body opt_return

        # expr_stmt is an expr where the value it produces
        # might not be needed. List-like things like
        # progn or let fall into this category.
        expr_stmt  ::= expr opt_discard


        # By its very nature of being sequenced
        # exprs must use a list-like or stmt_expr

        exprs ::= expr_stmt+


        progn ::= body

        expr  ::= save_excursion
        expr  ::= setq_expr
        expr  ::= binary_expr
        expr  ::= unary_expr
        expr  ::= nullary_expr
        expr  ::= name_expr

        expr  ::= if_expr
        expr  ::= if_else_expr
        expr  ::= cond_expr
        expr  ::= or_expr
        expr  ::= and_expr

        body  ::= exprs

        body_stacked  ::= expr_stacked exprs
        body_stacked  ::= expr_stacked

        expr_stacked ::= unary_expr_stacked
        expr_stacked ::= binary_expr_stacked
        expr_stacked ::= setq_expr_stacked

        save_excursion ::= SAVE-EXCURSION body UNBIND

        unary_expr_stacked ::= unary_op
        binary_expr_stacked ::= expr binary_op

        expr  ::= let_expr_star
        expr  ::= let_expr_stacked

        # if_expr ::= expr GOTO-IF-NIL-ELSE-POP expr LABEL
        # if_expr ::= expr GOTO-IF-NIL-ELSE-POP progn LABEL
        # if_expr ::= expr GOTO-IF-NIL expr LABEL
        # if_expr ::= expr GOTO-IF-NIL progn LABEL

        # if_else_expr ::= expr GOTO-IF-NIL expr RETURN LABEL
        # if_else_expr ::= expr_stacked GOTO-IF-NIL progn RETURN LABEL

        or_expr ::= expr GOTO-IF-NOT-NIL-ELSE-POP expr opt_come_from opt_label
        # or_expr ::= expr GOTO-IF-NOT-NIL expr opt_come_from opt_label

        and_expr ::= expr GOTO-IF-NIL-ELSE-POP expr COME_FROM LABEL
        # and_expr ::= expr GOTO-IF-NIL expr opt_label

        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= name_expr expr CALL_1
        call_expr2 ::= name_expr expr exp_stacked CALL_2
        call_expr3 ::= name_expr expr expr expr CALL_3

        name_expr ::= CONSTANT
        name_expr ::= VARREF

        binary_expr ::= expr expr binary_op

        binary_op ::= DIFF
        binary_op ::= EQLSIGN
        binary_op ::= EQ
        binary_op ::= EQUAL
        binary_op ::= GEQ
        binary_op ::= GTR
        binary_op ::= LEQ
        binary_op ::= LSS
        binary_op ::= MULT
        binary_op ::= PLUS
        binary_op ::= QUO
        binary_op ::= REM
        binary_op ::= TIMES

        unary_expr ::= expr unary_op

        unary_op ::= ADD1
        unary_op ::= CAR
        unary_op ::= CDR-SAFE
        unary_op ::= CDR
        unary_op ::= CONSP
        unary_op ::= INSERT
        unary_op ::= INTEGERP
        unary_op ::= KEYWORDP
        unary_op ::= LISTP
        unary_op ::= NATNUMP
        unary_op ::= NLISTP
        unary_op ::= NOT
        unary_op ::= NUMBERP
        unary_op ::= NULL
        unary_op ::= RECORDP
        unary_op ::= SEQUENCEP
        unary_op ::= STRINGP
        unary_op ::= SUBR-ARITY
        unary_op ::= SUBRP
        unary_op ::= SYMBOL-FUNCTION
        unary_op ::= SYMBOL-NAME
        unary_op ::= SYMBOL-PLIST
        unary_op ::= SYMBOLP
        unary_op ::= THREADP
        unary_op ::= TYPE-OF
        unary_op ::= USER-PTRP
        unary_op ::= VECTOR_OR_CHAR-TABLEP
        unary_op ::= VECTORP

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

        # FIXME: this is probably to permissive
        end_clause ::= GOTO COME_FROM
        end_clause ::= RETURN COME_FROM
        end_clause ::= RETURN
        end_clause ::= COME_FROM

        cond_expr  ::= clause labeled_clauses opt_label

        # We use labeled_clause+ rather than labeled_clause* because
        # labeled_clause* wreaks havoc in reductions and gives
        # produces things like (cond (t 5)) when what we want is just
        # 5. labeled_clause+ won't match (cond (foo bar baz)) where
        # there is a single cond clause but we'll handle that as an
        # "if" rule, e.g. (if foo (progn bar baz))

        labeled_clauses ::= labeled_clause+

        labeled_clause  ::= LABEL clause

        condition       ::= expr GOTO-IF-NIL
        condition       ::= expr GOTO-IF-NIL-ELSE-POP

        clause          ::= condition body end_clause

        # cond (t *body*) compiles to no condition
        # If this is the first clause, then possibly
        # no label
        clause          ::= opt_label body end_clause

        opt_come_from ::= COME_FROM?
        opt_label     ::= LABEL?

        let_expr_stacked ::= varlist_stacked body_stacked UNBIND

        varlist_stacked ::= expr varlist_stacked_inner DUP VARBIND
        varlist_stacked_inner ::= expr varlist_stacked_inner VARBIND
        varlist_stacked_inner ::=

        let_expr_star ::= varlist body UNBIND

        varlist  ::= varbind varlist
        varlist  ::= varbind
        varbind  ::= expr VARBIND

        opt_discard ::= DISCARD?
        opt_return  ::= RETURN?

        '''
        return

    def add_unique_rule(self, rule, opname):
        """Add rule to grammar, but only if it hasn't been added previously
           opname and count are used in the customize() semantic the actions
           to add the semantic action rule. Often, count is not used.
        """
        if rule not in self.new_rules:
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
        # self.check_reduce['progn'] = 'AST'
        self.check_reduce['clause'] = 'AST'
        return

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        lhs = rule[0]
        if ast and lhs == 'clause' and len(ast) == 3:
            # Check that either:
            #   if we have a condition there is a COME_FROM or
            #   if we don't have a condition there is no COME_FROM
            return (
                (ast[0] == 'condition' and
                 len(ast[2]) == 1 and ast[2][0] != 'COME_FROM') or
                (ast[0] != 'condition' and
                 ast[2][-1] == 'COME_FROM')
                )
        return False
    pass

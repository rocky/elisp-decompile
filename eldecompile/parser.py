"""Spark Earley Algorithm parser ELISP
"""
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, start='exprs', debug=PARSER_DEFAULT_DEBUG):
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(['exprs'])

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
        exprs ::= exprs expr
        exprs ::= expr

        expr  ::= setq_expr
        expr  ::= return_expr
        expr  ::= plus_expr
        expr  ::= name_expr

        # FIXME: add custom rule
        expr  ::= call_expr0
        expr  ::= call_expr1
        expr  ::= call_expr2
        expr  ::= call_expr3

        call_expr0 ::= name_expr CALL_0 DISCARD
        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= expr name_expr CALL_1 DISCARD
        call_expr2 ::= expr expr name_expr CALL_2 DISCARD
        call_expr3 ::= expr expr expr name_expr CALL_3 DISCARD

        name_expr ::= CONSTANT
        name_expr ::= VARREF


        plus_expr ::= expr expr PLUS

        setq_expr ::= expr VARSET
        setq_expr ::= expr DUP VARSET
        return_expr ::= RETURN
        '''
        return
    pass

"""Spark Earley Algorithm parser for Emacs LISP
"""

import re
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from lapdecompile.bb import compute_stack_change

nop_func = lambda self, args: None

class ParserError(Exception):
    def __init__(self, token, offset):
        self.token = token
        self.offset = offset

    def __str__(self):
        return "Parse error at or near `%r' instruction at offset %s\n" % \
               (self.token, self.offset)

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, tokens, start='fn_body', debug=PARSER_DEFAULT_DEBUG):
        self.tokens = tokens
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(["exprs", "varlist", "opt_exprs", "labeled_clauses"])
        self.new_rules = set()

    def error(self, tokens, index):
        # Find the last label
        start, finish = -1, -1
        n = len(tokens)
        for start in range(index, -1, -1):
            if tokens[start].label:  break
            pass
        for finish in range(index+1, len(tokens)):
            if tokens[finish].label:  break
            pass
        if start == finish == -1:
            start, finish = (0, n)
        elif start == -1:
            start = 0
        elif finish == -1:
            finish = n

        err_token = tokens[index]
        print("Instruction context:")
        for i in range(start, finish):
            if i != index:
                indent = '   '
            else:
                indent = '-> '
            print("%s%s" % (indent, tokens[i]))
        raise ParserError(err_token, err_token.offset)
        return

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
        fn_body ::= body opt_label opt_return
        fn_body ::= body opt_come_from opt_label stacked_return
        fn_body ::= body opt_come_from opt_label expr_return

        # expr_stmt is an expr where the value it produces
        # might not be needed. List-like things like
        # progn or let fall into this category.
        # expr_stmt's are maximimal in that the instruction after
        # the expr_stmt doesn't consume it unless it is consumed
        # for control-flow decision.
        # For example  "constant" is an "expr', but not an
        # "expr-stmt" unless it is followed by something like "return" or
        # "goto-if-nil", or "discard"
        #
        expr_stmt  ::= expr opt_discard

        # By its very nature of being sequenced
        # exprs must use a list-like or stmt_expr

        exprs     ::= expr_stmt+
        opt_exprs ::= expr_stmt*

        progn ::= body

        expr_stacked  ::= DUP
        expr_stacked  ::= unary_expr_stacked
        expr_stacked  ::= binary_expr_stacked
        expr_stacked  ::= ternary_expr_stacked
        expr_stacked  ::= set_expr_stacked

        expr  ::= DUP
        expr  ::= setq_form
        expr  ::= setq_form_dup
        expr  ::= set_expr
        expr  ::= STACK-REF
        expr  ::= VARREF

        # Function related
        expr  ::= binary_expr
        expr  ::= binary_expr_stacked
        expr  ::= ternary_expr
        expr  ::= unary_expr
        expr  ::= unary_expr_stacked
        expr  ::= nullary_expr
        expr  ::= name_expr
        expr  ::= pop_expr

        # Control-flow related
        expr  ::= if_form
        # expr  ::= if_else_form
        expr  ::= when_macro
        expr  ::= cond_form
        expr  ::= or_form
        expr  ::= and_form
        expr  ::= not_expr
        expr  ::= dolist_macro
        expr  ::= dolist_macro_result
        expr  ::= while_form1
        expr  ::= while_form2
        expr  ::= unwind_protect_form

        # Block related
        expr  ::= let_form_star
        expr  ::= let_form_stacked

        # Buffer related
        expr  ::= save_excursion_form
        expr  ::= save_current_buffer_form
        expr  ::= with_current_buffer_macro
        expr  ::= with_current_buffer_safe_macro
        expr  ::= set_buffer

        body  ::= exprs

        body_stacked  ::= expr_stacked opt_discard exprs
        body_stacked  ::= expr_stacked

        expr ::= setq_form_stacked

        save_excursion_form      ::= SAVE-EXCURSION body UNBIND
        save_current_buffer_form ::= SAVE-CURRENT-BUFFER body UNBIND
        with_current_buffer_macro ::= SAVE-CURRENT-BUFFER VARREF SET-BUFFER DISCARD exprs UNBIND
        with_current_buffer_safe_macro ::= VARREF NOT GOTO-IF-NOT-NIL-ELSE-POP
                                           CONSTANT VARREF CALL_1
                                           COME_FROM LABEL STACK-ACCESS
                                           NOT GOTO-IF-NIL-ELSE-POP
                                           with_current_buffer_macro
                                           opt_come_from opt_label

        set_buffer          ::= expr SET-BUFFER

        # FIXME: Are the STACK-ACCESS and without similar but
        # different notions of "expr_stacked"that should to be
        # disambiguated?

        unary_expr_stacked  ::= STACK-ACCESS unary_op
        unary_expr_stacked  ::= unary_op
        binary_expr_stacked ::= expr STACK-ACCESS binary_op
        binary_expr_stacked ::= expr_stacked binary_op


        # We keep nonterminals at position 0 and 2
        if_form ::= expr GOTO-IF-NIL expr opt_come_from opt_label
        filler  ::=
        if_form ::= expr filler expr_stmt COME_FROM LABEL

        # if_form ::= expr GOTO-IF-NIL-ELSE-POP expr LABEL
        # if_form ::= expr GOTO-IF-NIL-ELSE-POP progn LABEL
        if_form ::= expr GOTO-IF-NIL expr
        if_form ::= expr GOTO-IF-NOT-NIL expr opt_come_from opt_label

        while_form1 ::= expr COME_FROM LABEL expr
                        GOTO-IF-NIL-ELSE-POP body
                        GOTO COME_FROM LABEL

        while_form2 ::= COME_FROM LABEL expr
                        GOTO-IF-NIL-ELSE-POP body
                        GOTO COME_FROM LABEL

        when_macro ::= expr GOTO-IF-NIL body come_froms LABEL
        when_macro ::= expr GOTO-IF-NIL-ELSE-POP body come_froms LABEL


        unwind_protect_form ::= expr UNWIND-PROTECT opt_exprs

        # Note: the VARSET's have special names which we could
        # check in a reduce rule.
        dolist_macro ::= dolist_list dolist_init_var
                        GOTO-IF-NIL-ELSE-POP COME_FROM LABEL
                        dolist_loop_iter_set body
                        DUP VARSET GOTO-IF-NOT-NIL
                        CONSTANT COME_FROM LABEL
                        UNBIND

        dolist_macro ::= dolist_list dolist_init_var
                        GOTO-IF-NIL COME_FROM LABEL
                        dolist_loop_iter_set body
                        DUP VARSET GOTO-IF-NOT-NIL
                        COME_FROM LABEL
                        UNBIND

        dolist_macro ::= dolist_list dolist_init_var
                        GOTO-IF-NIL-ELSE-POP COME_FROM LABEL
                        dolist_loop_iter_set_stacking body_stacked
                        DUP VARSET GOTO-IF-NOT-NIL
                        CONSTANT COME_FROM LABEL
                        UNBIND


        dolist_macro_result ::= dolist_list dolist_init_var
                        GOTO-IF-NIL COME_FROM LABEL
                        dolist_loop_iter_set body
                        VARREF CDR DUP VARSET GOTO-IF-NOT-NIL
                        COME_FROM LABEL CONSTANT VARSET expr
                        UNBIND

        dolist_loop_iter_set ::= VARREF CAR VARSET
        dolist_loop_iter_set_stacking ::= VARREF CAR DUP VARSET
        dolist_init_var      ::= varbind DUP VARBIND
        dolist_list          ::= expr


        # if_else_form ::= expr GOTO-IF-NIL expr RETURN LABEL
        # if_else_form ::= expr_stacked GOTO-IF-NIL progn RETURN LABEL

        # FIXME: add something like this
        if_else_form ::= expr GOTO-IF-NIL-ELSE-POP expr-stmt RETURN

        # Keep nonterminals at positions  0 and 2
        or_form    ::= expr GOTO-IF-NOT-NIL-ELSE-POP expr opt_come_from opt_label
        or_form    ::= expr GOTO-IF-NOT-NIL          expr GOTO-IF-NIL-ELSE-POP COME_FROM LABEL
        or_form    ::= expr GOTO-IF-NOT-NIL expr

        # "not_expr" is (not expr) or (null expr). We use
        # not_ instead of null_ to to avoid confusion with nil
        not_expr   ::= expr GOTO-IF-NOT-NIL

        and_form   ::= expr GOTO-IF-NIL-ELSE-POP expr opt_come_from opt_label
        # and_form ::= expr GOTO-IF-NIL expr opt_label

        expr       ::= call_exprn
        expr       ::= call_expr0
        expr       ::= call_expr1
        expr       ::= call_expr2
        expr       ::= call_expr3
        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= name_expr expr CALL_1
        call_expr2 ::= name_expr expr exp_stacked CALL_2
        call_expr3 ::= name_expr expr expr expr CALL_3

        name_expr ::= CONSTANT

        expr_stacking ::= setq_form_stacking binary_op

        binary_expr ::= expr expr binary_op
        binary_expr_stacked  ::= STACK-ACCESS expr binary_op
        binary_expr ::= expr_stacking binary_op

        binary_op ::= DIFF
        binary_op ::= ELT
        binary_op ::= EQLSIGN
        binary_op ::= EQ
        binary_op ::= EQUAL
        binary_op ::= GEQ
        binary_op ::= GTR
        binary_op ::= LEQ
        binary_op ::= LSS
        binary_op ::= MAX
        binary_op ::= MIN
        binary_op ::= MULT
        binary_op ::= NCONC
        binary_op ::= PLUS
        binary_op ::= QUO
        binary_op ::= REM
        binary_op ::= STRING=
        binary_op ::= TIMES

        ternary_expr ::= expr expr expr ternary_op
        ternary_expr_stacked  ::= STACK-ACCESS expr expr ternary_op
        ternary_op   ::= SUBSTRING

        unary_expr ::= expr unary_op
        unary_expr ::= STACK-ACCESS unary_op

        unary_op ::= ADD1
        unary_op ::= CAR
        unary_op ::= CAR-SAFE
        unary_op ::= CDR
        unary_op ::= CDR-SAFE
        unary_op ::= CONSP
        unary_op ::= GOTO-CHAR
        unary_op ::= INSERT
        unary_op ::= INTEGERP
        unary_op ::= KEYWORDP
        unary_op ::= LENGTH
        unary_op ::= LISTP
        unary_op ::= NATNUMP
        unary_op ::= NLISTP
        unary_op ::= NOT
        unary_op ::= NUMBERP
        unary_op ::= NULL
        unary_op ::= RECORDP
        unary_op ::= SEQUENCEP
        unary_op ::= STACK-SET
        unary_op ::= STRINGP
        unary_op ::= SUBR-ARITY
        unary_op ::= SUB1
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

        nullary_op ::= BOLP
        nullary_op ::= CURRENT-BUFFER
        nullary_op ::= CURRENT-COLUMN
        nullary_op ::= EOLP
        nullary_op ::= FOLLOWING-CHAR
        nullary_op ::= POINT
        nullary_op ::= POINT-MAX
        nullary_op ::= POINT-MIN
        nullary_op ::= PRECEDING-CHAR
        nullary_op ::= WIDEN

        # We could have a checking rule that the VARREF and VARSET refer to the same thing
        pop_expr ::= VARREF DUP CDR VARSET CAR-SAFE

        setq_form ::= expr VARSET
        setq_form_dup ::= expr DUP VARSET
        setq_form_stacked ::= expr_stacked DUP VARSET
        setq_form_stacking ::= expr DUP VARSET

        set_expr  ::= expr expr SET
        set_expr  ::= expr expr STACK-SET SET
        set_expr_stacked  ::= expr_stacked expr SET


        # FIXME: this is probably to permissive
        end_clause ::= GOTO COME_FROM
        end_clause ::= RETURN COME_FROM
        end_clause ::= RETURN
        end_clause ::= stacked_return

        cond_form  ::= clause labeled_clauses come_froms LABEL
        cond_form  ::= clause labeled_clauses

        opt_come_froms ::= come_froms?
        come_froms ::= COME_FROM+

        # We use labeled_clause+ rather than labeled_clause* because
        # labeled_clause* wreaks havoc in reductions and gives
        # produces things like (cond (t 5)) when what we want is just
        # 5. labeled_clause+ won't match (cond (foo bar baz)) where
        # there is a single cond clause but we'll handle that as an
        # "if" rule, e.g. (if foo (progn bar baz))

        labeled_clauses ::= labeled_clause labeled_clauses
        labeled_clauses ::= labeled_clause
        labeled_clauses ::= labeled_final_clause

        labeled_clause  ::= LABEL clause

        # The "opt_come_from opt_label" below reflects the fact that
        # expr might be a short-circuit expression like "and" or "or"
        # which acts like and early false on the GOTO-IF-NIL

        condition       ::= expr GOTO-IF-NIL opt_come_from opt_label
        condition       ::= expr GOTO-IF-NIL-ELSE-POP opt_come_from opt_label

        clause          ::= condition body end_clause

        # The final clause of a cond doesn't need a GOTO or a return.
        # But it must have a label, and must have several COME_FROMs for
        # each of the clauses in the cond.
        labeled_final_clause    ::= LABEL condition body come_froms

        # clause          ::= body end_clause

        # cond (t *body*) compiles to no condition
        # If this is the first clause, then possibly
        # no label
        clause          ::= opt_label body end_clause

        opt_come_from ::= COME_FROM?
        opt_label     ::= LABEL?

        let_form_stacked ::= varlist_stacked body_stacked UNBIND

        varlist_stacked ::= expr varlist_stacked_inner DUP VARBIND
        varlist_stacked_inner ::= expr varlist_stacked_inner VARBIND
        varlist_stacked_inner ::=

        let_form_star ::= varlist body UNBIND
        # Sometimes the last item in "body" is "UNBIND" so we don't need
        # to add it here. We could have a reduce check to ensure this.
        let_form_star ::= varlist body

        varlist  ::= varbind varlist
        varlist  ::= varbind
        varbind  ::= expr VARBIND
        varbind  ::= expr STACK-ACCESS VARBIND

        opt_discard     ::= DISCARD?
        opt_return      ::= RETURN?

        stacked_return  ::= STACK-ACCESS RETURN
        expr_return     ::= expr RETURN

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
            if re.match(r"^LIST|CONCAT|CALL", opname):
                opname_base = opname[:opname.index('_')]
                if opname_base[-1] == 'N':
                    opname_base = opname_base[:-1]
                if opname_base == "CALL":
                    # Elisp calls add the function name as the 1st parameter.
                    # However Elisp convention is not to count that in
                    # the opcode.
                    v += 1
                nt = "%s_exprn" % (opname_base.lower())
                rule = '%s ::= %s%s' % (nt, ('expr ' * v), opname)
                self.add_unique_rule(rule, opname_base)
                rule = 'expr  ::= %s' % nt
                self.add_unique_rule(rule, opname_base)
            pass
        # self.check_reduce['progn'] = 'AST'
        self.check_reduce['while_form2'] = 'AST'
        self.check_reduce['clause'] = 'AST'
        self.check_reduce['cond_form'] = 'AST'
        self.check_reduce['if_form'] = 'AST'

        # "expr_stmt' is an expression used as a statement and
        # are derived from "expr". The intent of the reduction test
        # is to try to make sure the "expr_stmt" is used in a statement
        # kind of context. Without limiting these, limit larger expressions
        # might not form. Also we see a lot of extra (spurious reductions)
        # from expr_stmt->stmt->stmts->body.
        self.check_reduce['expr_stmt'] = 'tokens'
        self.check_reduce['save_current_buffer_form'] = 'tokens'
        self.check_reduce['setq_form'] = 'tokens'
        self.check_reduce['unary_expr_stacked'] = 'tokens'
        return

    def debug_reduce(self, rule, tokens, parent, last_token_pos):
        """Customized format and print for our kind of tokens
        which gets called in debugging grammar reduce rules
        """
        prefix = ''
        if parent and tokens:
            p_token = tokens[parent]
            if hasattr(p_token, 'offset'):
                prefix += "%3s" % p_token.offset
                if len(rule[1]) > 1:
                    prefix += '-%-5s ' % tokens[last_token_pos-1].offset
                else:
                    prefix += '       '
        else:
            prefix = '          '

        print("%s%s ::= %s (%d)" % (prefix, rule[0], ' '.join(rule[1]), last_token_pos))

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        lhs = rule[0]
        if lhs == 'clause' and len(ast) == 3 and ast[0] != 'opt_label':
            # Check that either:
            #   if we have a condition there is a COME_FROM in the end_clause or
            #   if we don't have a condition there is no COME_FROM in the end_clause
            end_clause = ast[2]
            if ast[0].kind == "condition" and len(end_clause) == 1:
                if (
                        end_clause[0] not in ("COME_FROM", "RETURN")
                        and last < len(tokens)
                        and tokens[last] != "RETURN"
                ):
                    return True
            if ast[0].kind != 'condition' and end_clause[-1] == 'COME_FROM':
                return True
        elif lhs == "unary_expr_stacked":
            # Check that previous token doesn't push something on the stack
            return first > 1 and tokens[first-1] != "VARSET"
        elif lhs == "if_form":
            # Check that GOTO goes to the right place
            if rule[1][1].startswith("GOTO"):
                if last == len(tokens):
                    return True
                if ast[1].offset != str(tokens[last+1].attr):
                    return True
            # "name_expr" isn't a valid "expr" for the "then" part of an "if_form"
            return ast[0] == "expr" and ast[0][0] == "name_expr"
        elif lhs == "while_form2":
            # Check that "expr" isn't a stacked expression.
            # Otherwise it should be handled by while_expr1
            expr = ast[2]
            while expr.kind.endswith("expr"):
                expr = expr[0]
            return expr.kind.endswith("stacked")
        elif lhs == "expr_stmt":
            stack_change = compute_stack_change(tokens[first:last])
            # Below, the various instructions test for instructions marking the
            # end of a basic block.
            # FIXME: should we do something more precise?
            if not (stack_change == 0
                or (stack_change > 0 and last < len(tokens) and
                    tokens[last] in (
                        "RETURN", "STACK-ACCESS", "UNBIND",
                        "COME_FROM", "GOTO", "LABEL", "DUP",
                        "GOTO-IF-NOT-NIL"
                    ))):
                if last >= len(tokens) or stack_change < 0:
                    return False
                if (tokens[last] == "DUP" and tokens[last+1] == "VARSET"):
                    # If dup is followed by "VARSET" it isn't an expr_stmt
                    # unless it is at the end and we are returning that value.
                    # FIXME: There must be a better way to express this.
                    # The VARSET might be generalized as an instruction which
                    # reads the value of DUP for example.
                    return last + 2 < len(tokens) and not (
                        tokens[last+2].kind in ("RETURN", "GOTO-IF-NOT-NIL")
                    )
                return True
        elif lhs == "save_current_buffer_form":
            # Invalidate rule if it matches with-current-buffer
            # Note: that the grammar rule isn't invalid, just not optimal.
            return ([tokens[i].kind for i in range(first+1, first+4)] == ["VARREF", "SET-BUFFER", "DISCARD"])

        elif lhs == "setq_form":
            if first == 0: return False
            return not (
                tokens[first-1] in
                ("LABEL", "VARSET", "VARBIND", "DISCARD") or tokens[first-1].kind.startswith("GOTO")
                )

        elif rule == ('cond_form', ('clause', 'labeled_clauses')):
            # Since there are no come froms, each of the clauses
            # must end in a return.
            for n in ast:
                if n == 'labeled_clauses':
                    n = n[0]
                if n == 'labeled_clause':
                    clause = n[1]
                elif n == 'clause':
                    clause = n
                else:
                    return False
                end_clause = clause[-1]
                if not (end_clause[0].kind in ("RETURN", "stacked_return")):
                    return True
                pass
        return False
    pass

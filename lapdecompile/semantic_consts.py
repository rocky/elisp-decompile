# -*- coding: utf-8 -*-
"""Semantic constants and syntax-directed table used to produce
string output.
"""

# Please don't blacken this file!
# It has custom formatting that blacken messes up.
TAB = ' ' *2   # is less spacy than "\t"
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level

TABLE_DIRECT = {
    "setq_form":	   ( "%(setq %Q %+%c%)", -1,
                             (0, "expr") ),
    "setq_form_stacked":   ( "%(setq %+%Q %c%)", -1, 0 ),
    "set_expr":            ( "%(set %+%c %c%)",
                             (0, "expr"), (1, "expr") ),
    "set_expr_stacked":    ( "%(set %+%c %c%)",
                             (0, "expr_stacked"), (1, "expr") ),
    "setq_form_dup":       ( "%(setq %+%c %c%p)",
                             -1, (0, "expr"), -1 ),
    "nullary_expr":	   ( "(%c)", 0 ),
    "unary_expr":	   ( "(%c %+%c%)", 1, 0 ),
    "unary_expr_stacked":  ( "(%c %+%S%)", 0 ),
    "binary_expr":	   ( "(%c %+%c %c%)",
                             (-1, "binary_op"),
                             (0, "expr"), (1, "expr") ),
    "binary_expr_stacked": ( "(%c %+%S %c%)", -1, 0),

    "ternary_expr":	   ( "(%c %+%c %c %c%)",
                             (-1, "ternary_op"),
                             (0, "expr"), (1, "expr"), (2, "expr") ),

    "concat_exprn":	   ( "(concat %l)", (0, 1000) ),

    # Created via transform only
    "defvar_doc":          ( "(defvar %Q%+\n%|%c\n%|%c%)",
                             (0, "CONSTANT"), (1, "expr"), (2, "CONSTANT") ),
    "defvar":              ( "(defvar %Q%+\n%|%c%)",
                             (0, "CONSTANT"), (1, "expr") ),
    "defconst_doc":        ( "(defconst %Q%+\n%|%c\n%|%c%)",
                             (0, "CONSTANT"), (1, "expr"), (2, "CONSTANT") ),
    "defconst":            ( "(defconst %Q%+\n%|%c%)",
                             (0, "CONSTANT"), (1, "expr") ),

    "list_exprn":	   ( "(list %l)", (0, 1000) ),
    "min_exprn":	   ( "(min %L)", (0, 1000) ),
    "max_exprn":	   ( "(max %L)", (0, 1000) ),
    "nconc_exprn":	   ( "(nconc %L)", (0, 1000) ),
    "set_buffer":          ( "(set-buffer %c)",
                             (0, "expr") ),

    "cond_form":	        ( "%(cond %.%c%c%)", 0, 1 ),
    "if_form":		        ( "%(if %c\n%+%|%c%)", 0, 2 ),
    "if_else_form":	        ( "%(if %c\n%+%|%c%_%c)%_", 0, 2, 5 ),
    "save_excursion_form":      ( "%(save-excursion\n%+%|%c%)",
                                  (1, "body") ),
    "save_current_buffer_form": ( "%(save-current-buffer\n%+%|%c%)",
                                  (1, "body") ),
    "with_current_buffer_macro":( "%(with-current-buffer %c\n%+%|%D%)",
                                  (1, "VARREF"), (4, 1000) ),

    "with_temp_buffer_macro":( "%(with-temp-buffer\n%+%|%c%)", 0),

    "labeled_clause":	   ( "%c", 1 ),
    "labeled_final_clause": ("\n%|(%c %c)", 1, 2),

    "while_form1":	  ( "%(while %p%c\n%+%|%c%)", 0, 3, 5 ),
    "while_form2":	  ( "%(while %c\n%+%|%c%)", 2, 4 ),

    # Need to handle multimple opt_exprs
    # "unwind_protect_form":( "%(unwind-protect\n%+%|%c%_%Q%)",
    #                             (2, "opt_exprs"), (0, "expr") ),

    "when_macro":	  ( "%(when %c\n%+%|%c%)", 0, 2 ),

    # "or_form":		  ( "(or %+%c %c%)", 0, 2 ),  # may need to push/pop values

    "and_form":		  ( "(and %+%c %c%)", 0, 2 ),
    "not_expr":		  ( "(null %+%c%)", 0 ),
    "dolist_macro_result": ( "%(dolist%+%(%c %c %c)\n%_%|%c)%_", 1, 0, 16, 6),

    "pop_expr":           ( "(pop %+%c%)", (0, "VARREF") ),

    "exprs":              ( "%C", (0, 1000) ),
    "expr_return":        ( "\n%|%c", (0, "expr") ),


    "let_form_stacked":	( "%(let %.(%.%c)%c%)", 0, 1 ),
    # "progn":		( "%(progn\n%+%|%c%)", 0 ),
    "body_stacked":	( "%c", 0 ),
    "stacked_return":	( ("", ) ),

    "ADD1":	( "1+" ,   ),
    "CAR":	( "car" ,  ),
    "CADR":	( "cadr" , ),
    "CAR-SAFE":	( "car-safe" , ),
    "DIFF":	( "-" ,  ),
    "EQLSIGN":	( "=" ,  ),
    "NEQLSIGN":	( "/=" , ),  # Can only occur via transform
    "GEQ":	( ">=" , ),
    "GTR":	( ">" ,  ),
    "LEQ":	( "<=" , ),
    "LSS":	( "<" ,  ),
    "MULT":	( "*" ,  ),
    "PLUS":	( "+" ,  ),
    "QUO":	( "/" ,  ),
    "REM":	( "%" ,  ),
    "SUB1":	( "1-" , ),

    "TSTRING":	        ( "%{attr}", ),
    "VARSET":	        ( "%{attr}", ),
    "VARBIND":	        ( "%{attr}", ),
    "VARREF":	        ( "%{attr}", ),
    "STACK-REF":	( "stack-ref%{attr}", ),
    "STACK-ACCESS":	( "%S", ),
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
goto-char insert integerp
keywordp length listp
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
aref elt eq equal fset max min nconc
remove-variable-watcher
setcar setcdr setplist string=
""".split())

TERNARY_OPS = tuple("""
substring
""".split())

for op in BINARY_OPS + TERNARY_OPS + UNARY_OPS + NULLARY_OPS:
    TABLE_DIRECT[op.upper()] = ( op, )

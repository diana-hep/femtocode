#!/usr/bin/env python
# generated at 2016-11-02T09:47:04 by "python generate-grammar/femtocode.g generate-grammar/actions.py femtocode/parser.py"

import re
import sys
import tokenize
from ast import literal_eval

from femtocode.thirdparty.ply import lex
from femtocode.thirdparty.ply import yacc

from femtocode.defs import FemtocodeError
from femtocode.defs import complain
from femtocode.asts.parsingtree import *

reserved = {
  'and': 'AND',
  'elif': 'ELIF',
  'is': 'IS',
  'else': 'ELSE',
  'in': 'IN',
  'not': 'NOT',
  'if': 'IF',
  'or': 'OR',
  'def': 'DEF',
  }

tokens = ['AND', 'ELIF', 'IS', 'ELSE', 'IN', 'NOT', 'IF', 'OR', 'DEF']

def t_MULTILINESTRING(t):
    r'(\'\'\'[^\\]*(\\.[^\\]*)*\'\'\'|"""[^\\]*(\\.[^\\]*)*""")'
    t.value = literal_eval(t.value), kwds(t.lexer, len(t.value))
    return t
tokens.append("MULTILINESTRING")

def t_STRING(t):
    r'(\'[^\n\'\\]*(\\.[^\n\'\\]*)*\'|"[^\n"\\]*(\\.[^\n"\\]*)*")'
    t.value = literal_eval(t.value), kwds(t.lexer, len(t.value))
    return t
tokens.append("STRING")

def t_IMAG_NUMBER(t):
    r"(\d+[jJ]|((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)[jJ])"
    t.value = float(t.value[:-1]) * 1j, kwds(t.lexer, len(t.value))
    return t
tokens.append("IMAG_NUMBER")

def t_FLOAT_NUMBER(t):
    r"((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)"
    t.value = float(t.value), kwds(t.lexer, len(t.value))
    return t
tokens.append("FLOAT_NUMBER")

def t_HEX_NUMBER(t):
    r"0[xX][0-9a-fA-F]+"
    t.value = int(t.value, 16), kwds(t.lexer, len(t.value))
    return t
tokens.append("HEX_NUMBER")

def t_OCT_NUMBER(t):
    r"0[oO][0-7]*"      # follow Python 3 rules: it is clearer
    t.value = int(t.value, 8), kwds(t.lexer, len(t.value))
    return t
tokens.append("OCT_NUMBER")

def t_DEC_NUMBER(t):
    r"(0+|[1-9][0-9]*)"
    t.value = int(t.value), kwds(t.lexer, len(t.value))
    return t
tokens.append("DEC_NUMBER")

def t_ATARG(t):
    r"\$[0-9]*"
    length = len(t.value)
    if len(t.value) == 1:
        t.value = None
    else:
        t.value = int(t.value[1:])
    t.value = t.value, kwds(t.lexer, length)
    return t
tokens.append("ATARG")

def t_NAME(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "NAME")
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t
tokens.append("NAME")

tokens.extend(['RIGHTARROW', 'GREATEREQUAL', 'EQEQUAL', 'LESSEQUAL', 'DOUBLESTAR', 'LSQB', 'DOT', 'NOTEQUAL', 'LBRACE', 'DOUBLESLASH', 'PERCENT', 'RSQB', 'RPAR', 'LPAR', 'PLUS', 'STAR', 'MINUS', 'COMMA', 'SLASH', 'LESS', 'RBRACE', 'SEMI', 'COLON', 'EQUAL', 'GREATER'])

literals = ['[', '.', '{', '%', ']', ')', '(', '+', '*', '-', ',', '/', '<', '}', ';', ':', '=', '>']

def t_RIGHTARROW(t):
    r"\=\>"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_GREATEREQUAL(t):
    r"\>\="
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_EQEQUAL(t):
    r"\=\="
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_LESSEQUAL(t):
    r"\<\="
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_DOUBLESTAR(t):
    r"\*\*"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_NOTEQUAL(t):
    r"\!\="
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_DOUBLESLASH(t):
    r"\/\/"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_LSQB(t):
    r"\["
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_DOT(t):
    r"\."
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_LBRACE(t):
    r"\{"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_PERCENT(t):
    r"\%"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_RSQB(t):
    r"\]"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_RPAR(t):
    r"\)"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_LPAR(t):
    r"\("
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_PLUS(t):
    r"\+"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_STAR(t):
    r"\*"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_MINUS(t):
    r"\-"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_COMMA(t):
    r"\,"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_SLASH(t):
    r"\/"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_LESS(t):
    r"\<"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_RBRACE(t):
    r"\}"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_SEMI(t):
    r"\;"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_COLON(t):
    r"\:"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_EQUAL(t):
    r"\="
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_GREATER(t):
    r"\>"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t

def t_error(t):
    complain("Unrecognizable token \"" + t.value + "\".", t.lexer.source, t.lexer.lexpos, t.lexer.lineno, t.lexer.lexpos - t.lexer.last_col0 + 1, t.lexer.sourceName, t.value[1]["length"])

def t_comment(t):
    r"[ ]*\043[^\n]*"  # \043 is # ; otherwise PLY thinks it is a regex comment
    pass

t_ignore = " \t\f"

def t_newline(t):
    r"\n"
    t.value = t.value, kwds(t.lexer, len(t.value))
    t.lexer.lineno += 1
    t.lexer.last_col0 = t.lexer.lexpos + 1

# body: ';'* suite
def p_body_1(p):
    '''body : suite'''
    #             1
    p[0] = p[1]
def p_body_2(p):
    '''body : body_star suite'''
    #                 1     2
    p[0] = p[2]

def p_body_star_1(p):
    '''body_star : SEMI'''
    #                 1
    p[0] = p[1]
def p_body_star_2(p):
    '''body_star : body_star SEMI'''
    #                      1    2
    p[0] = p[2]

# suite: (assignment ';'*)* expression ';'*
def p_suite_1(p):
    '''suite : expression'''
    #                   1
    p[0] = Suite([], p[1])
    inherit_lineno(p[0], p[1])
def p_suite_2(p):
    '''suite : expression suite_star'''
    #                   1          2
    p[0] = Suite([], p[1])
    inherit_lineno(p[0], p[1])
def p_suite_3(p):
    '''suite : suite_star2 expression'''
    #                    1          2
    p[0] = Suite(p[1], p[2])
    inherit_lineno(p[0], p[1][0])
def p_suite_4(p):
    '''suite : suite_star2 expression suite_star3'''
    #                    1          2           3
    p[0] = Suite(p[1], p[2])
    inherit_lineno(p[0], p[1][0])

def p_suite_star_1(p):
    '''suite_star : SEMI'''
    #                  1
    p[0] = None
def p_suite_star_2(p):
    '''suite_star : suite_star SEMI'''
    #                        1    2
    p[0] = None

def p_suite_star3_1(p):
    '''suite_star3 : SEMI'''
    #                   1
    p[0] = None
def p_suite_star3_2(p):
    '''suite_star3 : suite_star3 SEMI'''
    #                          1    2
    p[0] = None

def p_suite_star2_1(p):
    '''suite_star2 : assignment'''
    #                         1
    p[0] = [p[1]]
def p_suite_star2_2(p):
    '''suite_star2 : assignment suite_star2_star'''
    #                         1                2
    p[0] = [p[1]]
def p_suite_star2_3(p):
    '''suite_star2 : suite_star2 assignment'''
    #                          1          2
    p[0] = p[1] + [p[2]]
def p_suite_star2_4(p):
    '''suite_star2 : suite_star2 assignment suite_star2_star'''
    #                          1          2                3
    p[0] = p[1] + [p[2]]

def p_suite_star2_star_1(p):
    '''suite_star2_star : SEMI'''
    #                        1
    p[0] = None
def p_suite_star2_star_2(p):
    '''suite_star2_star : suite_star2_star SEMI'''
    #                                    1    2
    p[0] = None

# lvalues: (NAME ',')* NAME [',']                           // source of 1 shift/reduce conflict
def p_lvalues_1(p):
    '''lvalues : NAME'''
    #               1
    p[0] = [Name(p[1][0], Store(), **p[1][1])]
def p_lvalues_2(p):
    '''lvalues : NAME COMMA'''
    #               1     2
    p[0] = [Name(p[1][0], Store(), **p[1][1])]
def p_lvalues_3(p):
    '''lvalues : lvalues_star NAME'''
    #                       1    2
    p[0] = p[1] + [Name(p[2][0], Store(), **p[2][1])]
def p_lvalues_4(p):
    '''lvalues : lvalues_star NAME COMMA'''
    #                       1    2     3
    p[0] = p[1] + [Name(p[2][0], Store(), **p[2][1])]

def p_lvalues_star_1(p):
    '''lvalues_star : NAME COMMA'''
    #                    1     2
    p[0] = [Name(p[1][0], Store(), **p[1][1])]
def p_lvalues_star_2(p):
    '''lvalues_star : lvalues_star NAME COMMA'''
    #                            1    2     3
    p[0] = p[1] + [Name(p[2][0], Store(), **p[2][1])]

# assignment: lvalues '=' closed_expression | fcnndef
def p_assignment_1(p):
    '''assignment : lvalues EQUAL closed_expression'''
    #                     1     2                 3
    p[0] = Assignment(p[1], p[3])
    inherit_lineno(p[0], p[1][0])
def p_assignment_2(p):
    '''assignment : fcnndef'''
    #                     1
    p[0] = p[1]

# fcnndef: 'def' NAME '(' [paramlist] ')' closed_exprsuite
def p_fcnndef_1(p):
    '''fcnndef : DEF NAME LPAR RPAR closed_exprsuite'''
    #              1    2    3    4                5
    p[0] = Assignment([Name(p[2][0], Store(), **p[2][1])], FcnDef([], [], p[5], **p[1][1]), **p[1][1])
def p_fcnndef_2(p):
    '''fcnndef : DEF NAME LPAR paramlist RPAR closed_exprsuite'''
    #              1    2    3         4    5                6
    fcndef = p[4]
    fcndef.body = p[6]
    p[0] = Assignment([Name(p[2][0], Store(), **p[2][1])], fcndef, **p[1][1])

# expression: ifblock | fcndef | or_test
def p_expression_1(p):
    '''expression : ifblock'''
    #                     1
    p[0] = p[1]
def p_expression_2(p):
    '''expression : fcndef'''
    #                    1
    p[0] = p[1]
def p_expression_3(p):
    '''expression : or_test'''
    #                     1
    p[0] = p[1]

# closed_expression: closed_ifblock | fcndef | or_test ';'
def p_closed_expression_1(p):
    '''closed_expression : closed_ifblock'''
    #                                   1
    p[0] = p[1]
def p_closed_expression_2(p):
    '''closed_expression : fcndef'''
    #                           1
    p[0] = p[1]
def p_closed_expression_3(p):
    '''closed_expression : or_test SEMI'''
    #                            1    2
    p[0] = p[1]

# fcndef: '{' [paramlist] '=>' ';'* suite '}'
def p_fcndef_1(p):
    '''fcndef : LBRACE RIGHTARROW suite RBRACE'''
    #                1          2     3      4
    p[0] = FcnDef([], [], p[3], **p[1][1])
def p_fcndef_2(p):
    '''fcndef : LBRACE RIGHTARROW fcndef_star suite RBRACE'''
    #                1          2           3     4      5
    p[0] = FcnDef([], [], p[4], **p[1][1])
def p_fcndef_3(p):
    '''fcndef : LBRACE paramlist RIGHTARROW suite RBRACE'''
    #                1         2          3     4      5
    p[0] = p[2]
    p[0].body = p[4]
def p_fcndef_4(p):
    '''fcndef : LBRACE paramlist RIGHTARROW fcndef_star2 suite RBRACE'''
    #                1         2          3            4     5      6
    p[0] = p[2]
    p[0].body = p[5]

def p_fcndef_star_1(p):
    '''fcndef_star : SEMI'''
    #                   1
    p[0] = None
def p_fcndef_star_2(p):
    '''fcndef_star : fcndef_star SEMI'''
    #                          1    2
    p[0] = None

def p_fcndef_star2_1(p):
    '''fcndef_star2 : SEMI'''
    #                    1
    p[0] = None
def p_fcndef_star2_2(p):
    '''fcndef_star2 : fcndef_star2 SEMI'''
    #                            1    2
    p[0] = None

# fcn1def: parameter '=>' expression
def p_fcn1def(p):
    '''fcn1def : parameter RIGHTARROW expression'''
    #                    1          2          3
    p[0] = p[1]
    p[0].body = Suite([], p[3])
    inherit_lineno(p[0].body, p[3])

# paramlist: (parameter ',')* (parameter [','])
def p_paramlist_1(p):
    '''paramlist : parameter'''
    #                      1
    p[0] = p[1]
def p_paramlist_2(p):
    '''paramlist : parameter COMMA'''
    #                      1     2
    p[0] = p[1]
def p_paramlist_3(p):
    '''paramlist : paramlist_star parameter'''
    #                           1         2
    p[0] = p[1]
    p[0].parameters.extend(p[2].parameters)
    p[0].defaults.extend(p[2].defaults)
def p_paramlist_4(p):
    '''paramlist : paramlist_star parameter COMMA'''
    #                           1         2     3
    p[0] = p[1]
    p[0].parameters.extend(p[2].parameters)
    p[0].defaults.extend(p[2].defaults)

def p_paramlist_star_1(p):
    '''paramlist_star : parameter COMMA'''
    #                           1     2
    p[0] = p[1]
def p_paramlist_star_2(p):
    '''paramlist_star : paramlist_star parameter COMMA'''
    #                                1         2     3
    p[0] = p[1]
    p[0].parameters.extend(p[2].parameters)
    p[0].defaults.extend(p[2].defaults)

# parameter: NAME ['=' expression]                          // source of 1 shift/reduce conflict
def p_parameter_1(p):
    '''parameter : NAME'''
    #                 1
    p[0] = FcnDef([Name(p[1][0], Param(), **p[1][1])], [None], None, **p[1][1])
def p_parameter_2(p):
    '''parameter : NAME EQUAL expression'''
    #                 1     2          3
    p[0] = FcnDef([Name(p[1][0], Param(), **p[1][1])], [p[3]], None, **p[1][1])

# exprsuite: (':' expression | [':'] '{' ';'* suite '}')
def p_exprsuite_1(p):
    '''exprsuite : COLON expression'''
    #                  1          2
    p[0] = Suite([], p[2])
    inherit_lineno(p[0], p[2])
def p_exprsuite_2(p):
    '''exprsuite : LBRACE suite RBRACE'''
    #                   1     2      3
    p[0] = p[2]
def p_exprsuite_3(p):
    '''exprsuite : LBRACE exprsuite_star suite RBRACE'''
    #                   1              2     3      4
    p[0] = p[3]
def p_exprsuite_4(p):
    '''exprsuite : COLON LBRACE suite RBRACE'''
    #                  1      2     3      4
    p[0] = p[3]
def p_exprsuite_5(p):
    '''exprsuite : COLON LBRACE exprsuite_star2 suite RBRACE'''
    #                  1      2               3     4      5
    p[0] = p[4]

def p_exprsuite_star_1(p):
    '''exprsuite_star : SEMI'''
    #                      1
    p[0] = None
def p_exprsuite_star_2(p):
    '''exprsuite_star : exprsuite_star SEMI'''
    #                                1    2
    p[0] = None

def p_exprsuite_star2_1(p):
    '''exprsuite_star2 : SEMI'''
    #                       1
    p[0] = None
def p_exprsuite_star2_2(p):
    '''exprsuite_star2 : exprsuite_star2 SEMI'''
    #                                  1    2
    p[0] = None

# closed_exprsuite: (':' closed_expression | [':'] '{' ';'* suite '}')
def p_closed_exprsuite_1(p):
    '''closed_exprsuite : COLON closed_expression'''
    #                         1                 2
    p[0] = Suite([], p[2])
    inherit_lineno(p[0], p[2])
def p_closed_exprsuite_2(p):
    '''closed_exprsuite : LBRACE suite RBRACE'''
    #                          1     2      3
    p[0] = p[2]
def p_closed_exprsuite_3(p):
    '''closed_exprsuite : LBRACE closed_exprsuite_star suite RBRACE'''
    #                          1                     2     3      4
    p[0] = p[3]
def p_closed_exprsuite_4(p):
    '''closed_exprsuite : COLON LBRACE suite RBRACE'''
    #                         1      2     3      4
    p[0] = p[3]
def p_closed_exprsuite_5(p):
    '''closed_exprsuite : COLON LBRACE closed_exprsuite_star2 suite RBRACE'''
    #                         1      2                      3     4      5
    p[0] = p[4]

def p_closed_exprsuite_star_1(p):
    '''closed_exprsuite_star : SEMI'''
    #                             1
    p[0] = None
def p_closed_exprsuite_star_2(p):
    '''closed_exprsuite_star : closed_exprsuite_star SEMI'''
    #                                              1    2
    p[0] = None

def p_closed_exprsuite_star2_1(p):
    '''closed_exprsuite_star2 : SEMI'''
    #                              1
    p[0] = None
def p_closed_exprsuite_star2_2(p):
    '''closed_exprsuite_star2 : closed_exprsuite_star2 SEMI'''
    #                                                1    2
    p[0] = None

# ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' exprsuite)
def p_ifblock_1(p):
    '''ifblock : IF expression exprsuite ELSE exprsuite'''
    #             1          2         3    4         5
    p[0] = IfChain([p[2]], [p[3]], p[5], **p[1][1])
def p_ifblock_2(p):
    '''ifblock : IF expression exprsuite ifblock_star ELSE exprsuite'''
    #             1          2         3            4    5         6
    p[0] = IfChain([p[2]] + p[4][0], [p[3]] + p[4][1], p[6], **p[1][1])

def p_ifblock_star_1(p):
    '''ifblock_star : ELIF expression exprsuite'''
    #                    1          2         3
    p[0] = ([p[2]], [p[3]])
def p_ifblock_star_2(p):
    '''ifblock_star : ifblock_star ELIF expression exprsuite'''
    #                            1    2          3         4

    p[0] = p[1]
    p[0][0].append(p[3])
    p[0][1].append(p[4])

# closed_ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' closed_exprsuite)
def p_closed_ifblock_1(p):
    '''closed_ifblock : IF expression exprsuite ELSE closed_exprsuite'''
    #                    1          2         3    4                5
    p[0] = IfChain([p[2]], [p[3]], p[5], **p[1][1])
def p_closed_ifblock_2(p):
    '''closed_ifblock : IF expression exprsuite closed_ifblock_star ELSE closed_exprsuite'''
    #                    1          2         3                   4    5                6
    p[0] = IfChain([p[2]] + p[4][0], [p[3]] + p[4][1], p[6], **p[1][1])

def p_closed_ifblock_star_1(p):
    '''closed_ifblock_star : ELIF expression exprsuite'''
    #                           1          2         3
    p[0] = ([p[2]], [p[3]])
def p_closed_ifblock_star_2(p):
    '''closed_ifblock_star : closed_ifblock_star ELIF expression exprsuite'''
    #                                          1    2          3         4
    p[0] = p[1]
    p[0][0].append(p[3])
    p[0][1].append(p[4])

# or_test: and_test ('or' and_test)*
def p_or_test_1(p):
    '''or_test : and_test'''
    #                   1
    p[0] = p[1]
def p_or_test_2(p):
    '''or_test : and_test or_test_star'''
    #                   1            2
    theor = Or()
    p[0] = BoolOp(theor, [p[1]] + p[2])
    inherit_lineno(theor, p[1])
    inherit_lineno(p[0], p[1])

def p_or_test_star_1(p):
    '''or_test_star : OR and_test'''
    #                  1        2
    p[0] = [p[2]]
def p_or_test_star_2(p):
    '''or_test_star : or_test_star OR and_test'''
    #                            1  2        3
    p[0] = p[1] + [p[3]]

# and_test: not_test ('and' not_test)*
def p_and_test_1(p):
    '''and_test : not_test'''
    #                    1
    p[0] = p[1]
def p_and_test_2(p):
    '''and_test : not_test and_test_star'''
    #                    1             2
    theand = And()
    p[0] = BoolOp(theand, [p[1]] + p[2])
    inherit_lineno(theand, p[1])
    inherit_lineno(p[0], p[1])

def p_and_test_star_1(p):
    '''and_test_star : AND not_test'''
    #                    1        2
    p[0] = [p[2]]
def p_and_test_star_2(p):
    '''and_test_star : and_test_star AND not_test'''
    #                              1   2        3
    p[0] = p[1] + [p[3]]

# not_test: 'not' not_test | comparison
def p_not_test_1(p):
    '''not_test : NOT not_test'''
    #               1        2
    thenot = Not()
    inherit_lineno(thenot, p[2])
    p[0] = UnaryOp(thenot, p[2], **p[1][1])
def p_not_test_2(p):
    '''not_test : comparison'''
    #                      1
    p[0] = p[1]

# comparison: typecheck (comp_op typecheck)*
def p_comparison_1(p):
    '''comparison : typecheck'''
    #                       1
    p[0] = p[1]
def p_comparison_2(p):
    '''comparison : typecheck comparison_star'''
    #                       1               2
    ops, exprs = p[2]
    p[0] = Compare(p[1], ops, exprs)
    inherit_lineno(p[0], p[1])

def p_comparison_star_1(p):
    '''comparison_star : comp_op typecheck'''
    #                          1         2
    inherit_lineno(p[1], p[2])
    p[0] = ([p[1]], [p[2]])
def p_comparison_star_2(p):
    '''comparison_star : comparison_star comp_op typecheck'''
    #                                  1       2         3
    ops, exprs = p[1]
    inherit_lineno(p[2], p[3])
    p[0] = (ops + [p[2]], exprs + [p[3]])

# comp_op: '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in'
def p_comp_op_1(p):
    '''comp_op : LESS'''
    #               1
    p[0] = Lt()
def p_comp_op_2(p):
    '''comp_op : GREATER'''
    #                  1
    p[0] = Gt()
def p_comp_op_3(p):
    '''comp_op : EQEQUAL'''
    #                  1
    p[0] = Eq()
def p_comp_op_4(p):
    '''comp_op : GREATEREQUAL'''
    #                       1
    p[0] = GtE()
def p_comp_op_5(p):
    '''comp_op : LESSEQUAL'''
    #                    1
    p[0] = LtE()
def p_comp_op_6(p):
    '''comp_op : NOTEQUAL'''
    #                   1
    p[0] = NotEq()
def p_comp_op_7(p):
    '''comp_op : IN'''
    #             1
    p[0] = In()
def p_comp_op_8(p):
    '''comp_op : NOT IN'''
    #              1  2
    p[0] = NotIn()

# typecheck: arith_expr ['is' arith_expr | 'is' 'not' arith_expr]
def p_typecheck_1(p):
    '''typecheck : arith_expr'''
    #                       1
    p[0] = p[1]
def p_typecheck_2(p):
    '''typecheck : arith_expr IS arith_expr'''
    #                       1  2          3
    p[0] = TypeCheck(p[1], p[3], False)
    inherit_lineno(p[0], p[1])
def p_typecheck_3(p):
    '''typecheck : arith_expr IS NOT arith_expr'''
    #                       1  2   3          4
    p[0] = TypeCheck(p[1], p[4], True)
    inherit_lineno(p[0], p[1])

# arith_expr: term (('+' | '-') term)*
def p_arith_expr_1(p):
    '''arith_expr : term'''
    #                  1
    p[0] = p[1]
def p_arith_expr_2(p):
    '''arith_expr : term arith_expr_star'''
    #                  1               2
    p[0] = unwrap_left_associative([p[1]] + p[2], alt=len(p[2]) > 2)

def p_arith_expr_star_1(p):
    '''arith_expr_star : PLUS term'''
    #                       1    2
    p[0] = [Add(**p[1][1]), p[2]]
def p_arith_expr_star_2(p):
    '''arith_expr_star : MINUS term'''
    #                        1    2
    p[0] = [Sub(**p[1][1]), p[2]]
def p_arith_expr_star_3(p):
    '''arith_expr_star : arith_expr_star PLUS term'''
    #                                  1    2    3
    p[0] = p[1] + [Add(**p[2][1]), p[3]]
def p_arith_expr_star_4(p):
    '''arith_expr_star : arith_expr_star MINUS term'''
    #                                  1     2    3
    p[0] = p[1] + [Sub(**p[2][1]), p[3]]

# term: factor (('*' | '/' | '%' | '//') factor)*
def p_term_1(p):
    '''term : factor'''
    #              1
    p[0] = p[1]
def p_term_2(p):
    '''term : factor term_star'''
    #              1         2
    p[0] = unwrap_left_associative([p[1]] + p[2], alt=len(p[2]) > 2)

def p_term_star_1(p):
    '''term_star : STAR factor'''
    #                 1      2
    p[0] = [Mult(**p[1][1]), p[2]]
def p_term_star_2(p):
    '''term_star : SLASH factor'''
    #                  1      2
    p[0] = [Div(**p[1][1]), p[2]]
def p_term_star_3(p):
    '''term_star : PERCENT factor'''
    #                    1      2
    p[0] = [Mod(**p[1][1]), p[2]]
def p_term_star_4(p):
    '''term_star : DOUBLESLASH factor'''
    #                        1      2
    p[0] = [FloorDiv(**p[1][1]), p[2]]
def p_term_star_5(p):
    '''term_star : term_star STAR factor'''
    #                      1    2      3
    p[0] = p[1] + [Mult(**p[2][1]), p[3]]
def p_term_star_6(p):
    '''term_star : term_star SLASH factor'''
    #                      1     2      3
    p[0] = p[1] + [Div(**p[2][1]), p[3]]
def p_term_star_7(p):
    '''term_star : term_star PERCENT factor'''
    #                      1       2      3
    p[0] = p[1] + [Mod(**p[2][1]), p[3]]
def p_term_star_8(p):
    '''term_star : term_star DOUBLESLASH factor'''
    #                      1           2      3
    p[0] = p[1] + [FloorDiv(**p[2][1]), p[3]]

# factor: ('+' | '-') factor | power
def p_factor_1(p):
    '''factor : PLUS factor'''
    #              1      2
    op = UAdd(**p[1][1])
    p[0] = UnaryOp(op, p[2])
    inherit_lineno(p[0], op)
def p_factor_2(p):
    '''factor : MINUS factor'''
    #               1      2
    if sys.version_info.major <= 2 and isinstance(p[2], Num) and not hasattr(p[2], "unary"):
        p[2].n *= -1
        p[0] = p[2]
        p[0].unary = True
        inherit_lineno(p[0], p[1][1])
    else:
        op = USub(**p[1][1])
        p[0] = UnaryOp(op, p[2])
        inherit_lineno(p[0], op)
def p_factor_3(p):
    '''factor : power'''
    #               1
    p[0] = p[1]

# power: atom trailer* ['**' factor]
def p_power_1(p):
    '''power : atom'''
    #             1
    p[0] = p[1]
def p_power_2(p):
    '''power : atom DOUBLESTAR factor'''
    #             1          2      3
    p[0] = BinOp(p[1], Pow(**p[2][1]), p[3])
    inherit_lineno(p[0], p[1])
def p_power_3(p):
    '''power : atom power_star'''
    #             1          2
    p[0] = unpack_trailer(p[1], p[2])
def p_power_4(p):
    '''power : atom power_star DOUBLESTAR factor'''
    #             1          2          3      4
    p[0] = BinOp(unpack_trailer(p[1], p[2]), Pow(**p[3][1]), p[4])
    inherit_lineno(p[0], p[1])

def p_power_star_1(p):
    '''power_star : trailer'''
    #                     1
    p[0] = [p[1]]
def p_power_star_2(p):
    '''power_star : power_star trailer'''
    #                        1       2
    p[0] = p[1] + [p[2]]

# atom: ('(' expression ')'
#         | '[' (expression ',')* [expression [',']] ']'
#         | fcndef '(' [arglist] ')'                        // source of 1 shift/reduce conflict
#         | MULTILINESTRING
#         | STRING
#         | IMAG_NUMBER
#         | FLOAT_NUMBER
#         | HEX_NUMBER
#         | OCT_NUMBER
#         | DEC_NUMBER
#         | ATARG
#         | NAME)
def p_atom_1(p):
    '''atom : LPAR expression RPAR'''
    #            1          2    3
    p[0] = p[2]
    p[0].alt = p[1][1]
def p_atom_2(p):
    '''atom : LSQB RSQB'''
    #            1    2
    p[0] = List([], Load(), **p[1][1])
def p_atom_3(p):
    '''atom : LSQB expression RSQB'''
    #            1          2    3
    p[0] = List([p[2]], Load(), **p[1][1])
def p_atom_4(p):
    '''atom : LSQB expression COMMA RSQB'''
    #            1          2     3    4
    p[0] = List([p[2]], Load(), **p[1][1])
def p_atom_6(p):
    '''atom : LSQB atom_star expression RSQB'''
    #            1         2          3    4
    p[2].append(p[3])
    p[0] = List(p[2], Load(), **p[1][1])
def p_atom_7(p):
    '''atom : LSQB atom_star expression COMMA RSQB'''
    #            1         2          3     4    5
    p[2].append(p[3])
    p[0] = List(p[2], Load(), **p[1][1])
def p_atom_8(p):
    '''atom : fcndef LPAR RPAR'''
    #              1    2    3
    p[0] = FcnCall(p[1], [], [], [])
    inherit_lineno(p[0], p[1])
def p_atom_9(p):
    '''atom : fcndef LPAR arglist RPAR'''
    #              1    2       3    4

    p[0] = p[3]
    p[0].function = p[1]
def p_atom_10(p):
    '''atom : MULTILINESTRING'''
    #                       1
    p[0] = Str(p[1][0], **p[1][1])
def p_atom_11(p):
    '''atom : STRING'''
    #              1
    p[0] = Str(p[1][0], **p[1][1])
def p_atom_12(p):
    '''atom : IMAG_NUMBER'''
    #                   1
    p[0] = Num(p[1][0], **p[1][1])
def p_atom_13(p):
    '''atom : FLOAT_NUMBER'''
    #                    1
    p[0] = Num(p[1][0], **p[1][1])
def p_atom_14(p):
    '''atom : HEX_NUMBER'''
    #                  1
    p[0] = Num(p[1][0], **p[1][1])
def p_atom_15(p):
    '''atom : OCT_NUMBER'''
    #                  1
    p[0] = Num(p[1][0], **p[1][1])
def p_atom_16(p):
    '''atom : DEC_NUMBER'''
    #                  1
    p[0] = Num(p[1][0], **p[1][1])
def p_atom_17(p):
    '''atom : ATARG'''
    #             1
    p[0] = AtArg(p[1][0], **p[1][1])
def p_atom_18(p):
    '''atom : NAME'''
    #            1
    p[0] = Name(p[1][0], Load(), **p[1][1])

def p_atom_star_1(p):
    '''atom_star : expression COMMA'''
    #                       1     2
    p[0] = [p[1]]
def p_atom_star_2(p):
    '''atom_star : atom_star expression COMMA'''
    #                      1          2     3
    p[1].append(p[2])
    p[0] = p[1]

# trailer: '(' [arglist] ')' | '[' subscriptlist ']' | '.' NAME
def p_trailer_1(p):
    '''trailer : LPAR RPAR'''
    #               1    2
    p[0] = FcnCall(None, [], [], [], **p[1][1])
def p_trailer_2(p):
    '''trailer : LPAR arglist RPAR'''
    #               1       2    3
    p[0] = p[2]
def p_trailer_3(p):
    '''trailer : LSQB subscriptlist RSQB'''
    #               1             2    3
    p[0] = Subscript(None, p[2], Load())
def p_trailer_4(p):
    '''trailer : DOT NAME'''
    #              1    2
    p[0] = Attribute(None, p[2][0], Load())

# subscriptlist: subscript (',' subscript)* [',']
def p_subscriptlist_1(p):
    '''subscriptlist : subscript'''
    #                          1
    p[0] = p[1]
def p_subscriptlist_2(p):
    '''subscriptlist : subscript COMMA'''
    #                          1     2
    if isinstance(p[1], Index):
        tup = Tuple([p[1].value], Load())
        inherit_lineno(tup, p[1].value)
        p[0] = Index(tup)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice([p[1]])
        inherit_lineno(p[0], p[1])
def p_subscriptlist_3(p):
    '''subscriptlist : subscript subscriptlist_star'''
    #                          1                  2
    args = [p[1]] + p[2]
    if all(isinstance(x, Index) for x in args):
        tup = Tuple([x.value for x in args], Load())
        inherit_lineno(tup, args[0].value)
        p[0] = Index(tup)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice(args)
        inherit_lineno(p[0], p[1])
def p_subscriptlist_4(p):
    '''subscriptlist : subscript subscriptlist_star COMMA'''
    #                          1                  2     3
    args = [p[1]] + p[2]
    if all(isinstance(x, Index) for x in args):
        tup = Tuple([x.value for x in args], Load())
        inherit_lineno(tup, args[0].value)
        p[0] = Index(tup)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ExtSlice(args)
        inherit_lineno(p[0], p[1])

def p_subscriptlist_star_1(p):
    '''subscriptlist_star : COMMA subscript'''
    #                           1         2
    p[0] = [p[2]]
def p_subscriptlist_star_2(p):
    '''subscriptlist_star : subscriptlist_star COMMA subscript'''
    #                                        1     2         3
    p[0] = p[1] + [p[3]]

# subscript: expression | [expression] ':' [expression] [sliceop]
def p_subscript_1(p):
    '''subscript : expression'''
    #                       1
    p[0] = Index(p[1])
    inherit_lineno(p[0], p[1])
def p_subscript_2(p):
    '''subscript : COLON'''
    #                  1
    p[0] = Slice(None, None, None, **p[1][1])
def p_subscript_3(p):
    '''subscript : COLON sliceop'''
    #                  1       2
    p[0] = Slice(None, None, p[2], **p[1][1])
def p_subscript_4(p):
    '''subscript : COLON expression'''
    #                  1          2
    p[0] = Slice(None, p[2], None, **p[1][1])
def p_subscript_5(p):
    '''subscript : COLON expression sliceop'''
    #                  1          2       3
    p[0] = Slice(None, p[2], p[3], **p[1][1])
def p_subscript_6(p):
    '''subscript : expression COLON'''
    #                       1     2
    p[0] = Slice(p[1], None, None)
    inherit_lineno(p[0], p[1])
def p_subscript_7(p):
    '''subscript : expression COLON sliceop'''
    #                       1     2       3
    p[0] = Slice(p[1], None, p[3])
    inherit_lineno(p[0], p[1])
def p_subscript_8(p):
    '''subscript : expression COLON expression'''
    #                       1     2          3
    p[0] = Slice(p[1], p[3], None)
    inherit_lineno(p[0], p[1])
def p_subscript_9(p):
    '''subscript : expression COLON expression sliceop'''
    #                       1     2          3       4
    p[0] = Slice(p[1], p[3], p[4])
    inherit_lineno(p[0], p[1])

# sliceop: ':' [expression]
def p_sliceop_1(p):
    '''sliceop : COLON'''
    #                1
    p[0] = Name("None", Load(), **p[1][1]) if sys.version_info.major <= 2 else None
def p_sliceop_2(p):
    '''sliceop : COLON expression'''
    #                1          2
    p[0] = p[2]

# arglist: ((argument ',')* (argument [','])) | fcn1def
def p_arglist_1(p):
    '''arglist : argument'''
    #                   1
    p[0] = p[1]
def p_arglist_2(p):
    '''arglist : argument COMMA'''
    #                   1     2
    p[0] = p[1]
def p_arglist_3(p):
    '''arglist : arglist_star argument'''
    #                       1        2
    p[0] = p[1]
    p[0].positional.extend(p[2].positional)
    p[0].names.extend(p[2].names)
    p[0].named.extend(p[2].named)
def p_arglist_4(p):
    '''arglist : arglist_star argument COMMA'''
    #                       1        2     3
    p[0] = p[1]
    p[0].positional.extend(p[2].positional)
    p[0].names.extend(p[2].names)
    p[0].named.extend(p[2].named)
def p_arglist_5(p):
    '''arglist : fcn1def'''
    #                  1
    p[0] = FcnCall(None, [p[1]], [], [])
    inherit_lineno(p[0], p[1])

def p_arglist_star_1(p):
    '''arglist_star : argument COMMA'''
    #                        1     2
    p[0] = p[1]
def p_arglist_star_2(p):
    '''arglist_star : arglist_star argument COMMA'''
    #                            1        2     3
    p[0] = p[1]
    p[0].positional.extend(p[2].positional)
    p[0].names.extend(p[2].names)
    p[0].named.extend(p[2].named)

# argument: expression | NAME '=' expression
def p_argument_1(p):
    '''argument : expression'''
    #                      1
    p[0] = FcnCall(None, [p[1]], [], [])
    inherit_lineno(p[0], p[1])
def p_argument_2(p):
    '''argument : NAME EQUAL expression'''
    #                1     2          3
    p[0] = FcnCall(None, [], [Name(p[1][0], Param(), **p[1][1])], [p[3]], **p[1][1])

def p_error(p):
    if p is None:
        raise FemtocodeError("Code block did not end with an expression.")
    else:
        complain("This token not expected here.", p.lexer.source, p.lexer.lexpos, p.lexer.lineno, p.lexer.lexpos - p.lexer.last_col0 + 1 - p.value[1]["length"], p.lexer.sourceName, 1)

def kwds(lexer, length):
    return {"source": lexer.source, "pos": lexer.lexpos - length, "lineno": lexer.lineno, "col_offset": lexer.lexpos - lexer.last_col0 + 1 - length, "sourceName": lexer.sourceName, "length": length}

def parse(source, sourceName="<string>"):
    lexer = lex.lex()
    lexer.source = source
    lexer.sourceName = sourceName
    lexer.lineno = 1
    lexer.last_col0 = 1
    parser = yacc.yacc(debug=False, write_tables=True, tabmodule="parsertable", errorlog=yacc.NullLogger())
    return parser.parse(source, lexer=lexer)


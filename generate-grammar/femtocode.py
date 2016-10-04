#!/usr/bin/env python
# generated at NOW by "python femtocode.g femtocode.py"

import re
import ast

from ply import lex
from ply import yacc


reserved = {
  'and': 'AND',
  'elif': 'ELIF',
  'else': 'ELSE',
  'in': 'IN',
  'not': 'NOT',
  'if': 'IF',
  'or': 'OR',
  'def': 'DEF',
  }

tokens = ['AND', 'ELIF', 'ELSE', 'IN', 'NOT', 'IF', 'OR', 'DEF']

def t_STRING(t):
    r'([uUbB]?[rR]?\'[^\\n\'\\\\]*(?:\\\\.[^\\n\'\\\\]*)*\'|[uUbB]?[rR]?"[^\\n"\\\\]*(?:\\\\.[^\\n"\\\\]*)*")'
    return t
tokens.append("STRING")

def t_IMAG_NUMBER(t):
    r"(\d+[jJ]|((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)[jJ])"
    return t
tokens.append("IMAG_NUMBER")

def t_FLOAT_NUMBER(t):
    r"((\d+\.\d*|\.\d+)([eE][-+]?\d+)?|\d+[eE][-+]?\d+)"
    return t
tokens.append("FLOAT_NUMBER")

def t_HEX_NUMBER(t):
    r"0[xX][0-9a-fA-F]+"
    return t
tokens.append("HEX_NUMBER")

def t_OCT_NUMBER(t):
    r"0o?[0-7]*"
    return t
tokens.append("OCT_NUMBER")

def t_DEC_NUMBER(t):
    r"[1-9][0-9]*"
    return t
tokens.append("DEC_NUMBER")

def t_ATARG(t):
    r"@[0-9]*"
    return t
tokens.append("ATARG")

def t_NAME(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "NAME")
    return t
tokens.append("NAME")

tokens.extend(['RIGHTARROW', 'GREATEREQUAL', 'EQEQUAL', 'LESSEQUAL', 'DOUBLESTAR', 'LSQB', 'DOT', 'NOTEQUAL', 'LBRACE', 'DOUBLESLASH', 'PERCENT', 'RSQB', 'RPAR', 'LPAR', 'PLUS', 'STAR', 'MINUS', 'COMMA', 'SLASH', 'LESS', 'RBRACE', 'SEMI', 'COLON', 'EQUAL', 'GREATER'])

literals = ['[', '.', '{', '%', ']', ')', '(', '+', '*', '-', ',', '/', '<', '}', ';', ':', '=', '>']

def t_RIGHTARROW(t):
    r"\=\>"
    return t

def t_GREATEREQUAL(t):
    r"\>\="
    return t

def t_EQEQUAL(t):
    r"\=\="
    return t

def t_LESSEQUAL(t):
    r"\<\="
    return t

def t_DOUBLESTAR(t):
    r"\*\*"
    return t

def t_NOTEQUAL(t):
    r"\!\="
    return t

def t_DOUBLESLASH(t):
    r"\/\/"
    return t

def t_LSQB(t):
    r"\["
    return t

def t_DOT(t):
    r"\."
    return t

def t_LBRACE(t):
    r"\{"
    return t

def t_PERCENT(t):
    r"\%"
    return t

def t_RSQB(t):
    r"\]"
    return t

def t_RPAR(t):
    r"\)"
    return t

def t_LPAR(t):
    r"\("
    return t

def t_PLUS(t):
    r"\+"
    return t

def t_STAR(t):
    r"\*"
    return t

def t_MINUS(t):
    r"\-"
    return t

def t_COMMA(t):
    r"\,"
    return t

def t_SLASH(t):
    r"\/"
    return t

def t_LESS(t):
    r"\<"
    return t

def t_RBRACE(t):
    r"\}"
    return t

def t_SEMI(t):
    r"\;"
    return t

def t_COLON(t):
    r"\:"
    return t

def t_EQUAL(t):
    r"\="
    return t

def t_GREATER(t):
    r"\>"
    return t

def t_NL(t):
    r"\n"
    return t

def t_error(t):
    raise SyntaxError(t)

def t_comment(t):
    r"[ ]*\043[^\n]*"  # \043 is # ; otherwise PLY thinks it is a regex comment
    pass

t_ignore = " \t\f\n"


# body: ';'* suite
def p_body_1(p):
    '''body : suite'''
    #             1
    print("body : suite")
def p_body_2(p):
    '''body : body_star suite'''
    #                 1     2
    print("body : body_star suite")

def p_body_star_1(p):
    '''body_star : SEMI'''
    #                 1
    print("body_star : SEMI")
def p_body_star_2(p):
    '''body_star : body_star SEMI'''
    #                      1    2
    print("body_star : body_star SEMI")

# suite: (assignment ';'*)* expression ';'*
def p_suite_1(p):
    '''suite : expression'''
    #                   1
    print("suite : expression")
def p_suite_2(p):
    '''suite : expression suite_star'''
    #                   1          2
    print("suite : expression suite_star")
def p_suite_3(p):
    '''suite : suite_star2 expression'''
    #                    1          2
    print("suite : suite_star2 expression")
def p_suite_4(p):
    '''suite : suite_star2 expression suite_star3'''
    #                    1          2           3
    print("suite : suite_star2 expression suite_star3")

def p_suite_star_1(p):
    '''suite_star : SEMI'''
    #                  1
    print("suite_star : SEMI")
def p_suite_star_2(p):
    '''suite_star : suite_star SEMI'''
    #                        1    2
    print("suite_star : suite_star SEMI")

def p_suite_star3_1(p):
    '''suite_star3 : SEMI'''
    #                   1
    print("suite_star3 : SEMI")
def p_suite_star3_2(p):
    '''suite_star3 : suite_star3 SEMI'''
    #                          1    2
    print("suite_star3 : suite_star3 SEMI")

def p_suite_star2_1(p):
    '''suite_star2 : assignment'''
    #                         1
    print("suite_star2 : assignment")
def p_suite_star2_2(p):
    '''suite_star2 : assignment suite_star2_star'''
    #                         1                2
    print("suite_star2 : assignment suite_star2_star")
def p_suite_star2_3(p):
    '''suite_star2 : suite_star2 assignment'''
    #                          1          2
    print("suite_star2 : suite_star2 assignment")
def p_suite_star2_4(p):
    '''suite_star2 : suite_star2 assignment suite_star2_star'''
    #                          1          2                3
    print("suite_star2 : suite_star2 assignment suite_star2_star")

def p_suite_star2_star_1(p):
    '''suite_star2_star : SEMI'''
    #                        1
    print("suite_star2_star : SEMI")
def p_suite_star2_star_2(p):
    '''suite_star2_star : suite_star2_star SEMI'''
    #                                    1    2
    print("suite_star2_star : suite_star2_star SEMI")

# assignment: NAME '=' closed_expression | fcnndef
def p_assignment_1(p):
    '''assignment : NAME EQUAL closed_expression'''
    #                  1     2                 3
    print("assignment : NAME EQUAL closed_expression")
def p_assignment_2(p):
    '''assignment : fcnndef'''
    #                     1
    print("assignment : fcnndef")

# fcnndef: 'def' NAME '(' paramlist ')' closed_exprsuite
def p_fcnndef(p):
    '''fcnndef : DEF NAME LPAR paramlist RPAR closed_exprsuite'''
    #              1    2    3         4    5                6
    print("fcnndef : DEF NAME LPAR paramlist RPAR closed_exprsuite")

# expression: ifblock | fcndef | or_test
def p_expression_1(p):
    '''expression : ifblock'''
    #                     1
    print("expression : ifblock")
def p_expression_2(p):
    '''expression : fcndef'''
    #                    1
    print("expression : fcndef")
def p_expression_3(p):
    '''expression : or_test'''
    #                     1
    print("expression : or_test")

# closed_expression: closed_ifblock | fcndef | or_test ';'
def p_closed_expression_1(p):
    '''closed_expression : closed_ifblock'''
    #                                   1
    print("closed_expression : closed_ifblock")
def p_closed_expression_2(p):
    '''closed_expression : fcndef'''
    #                           1
    print("closed_expression : fcndef")
def p_closed_expression_3(p):
    '''closed_expression : or_test SEMI'''
    #                            1    2
    print("closed_expression : or_test SEMI")

# fcndef: '{' paramlist '=>' suite '}'
def p_fcndef(p):
    '''fcndef : LBRACE paramlist RIGHTARROW suite RBRACE'''
    #                1         2          3     4      5
    print("fcndef : LBRACE paramlist RIGHTARROW suite RBRACE")

# fcn1def: parameter '=>' (expression | '{' suite '}')
def p_fcn1def_1(p):
    '''fcn1def : parameter RIGHTARROW expression'''
    #                    1          2          3
    print("fcn1def : parameter RIGHTARROW expression")
def p_fcn1def_2(p):
    '''fcn1def : parameter RIGHTARROW LBRACE suite RBRACE'''
    #                    1          2      3     4      5
    print("fcn1def : parameter RIGHTARROW LBRACE suite RBRACE")

# paramlist: (parameter ',')* (parameter [','])
def p_paramlist_1(p):
    '''paramlist : parameter'''
    #                      1
    print("paramlist : parameter")
def p_paramlist_2(p):
    '''paramlist : parameter COMMA'''
    #                      1     2
    print("paramlist : parameter COMMA")
def p_paramlist_3(p):
    '''paramlist : paramlist_star parameter'''
    #                           1         2
    print("paramlist : paramlist_star parameter")
def p_paramlist_4(p):
    '''paramlist : paramlist_star parameter COMMA'''
    #                           1         2     3
    print("paramlist : paramlist_star parameter COMMA")

def p_paramlist_star_1(p):
    '''paramlist_star : parameter COMMA'''
    #                           1     2
    print("paramlist_star : parameter COMMA")
def p_paramlist_star_2(p):
    '''paramlist_star : paramlist_star parameter COMMA'''
    #                                1         2     3
    print("paramlist_star : paramlist_star parameter COMMA")

# parameter: NAME
def p_parameter(p):
    '''parameter : NAME'''
    #                 1
    print("parameter : NAME")

# exprsuite: (':' expression | [':'] '{' suite '}')
def p_exprsuite_1(p):
    '''exprsuite : COLON expression'''
    #                  1          2
    print("exprsuite : COLON expression")
def p_exprsuite_2(p):
    '''exprsuite : LBRACE suite RBRACE'''
    #                   1     2      3
    print("exprsuite : LBRACE suite RBRACE")
def p_exprsuite_3(p):
    '''exprsuite : COLON LBRACE suite RBRACE'''
    #                  1      2     3      4
    print("exprsuite : COLON LBRACE suite RBRACE")

# closed_exprsuite: (':' closed_expression | [':'] '{' suite '}')
def p_closed_exprsuite_1(p):
    '''closed_exprsuite : COLON closed_expression'''
    #                         1                 2
    print("closed_exprsuite : COLON closed_expression")
def p_closed_exprsuite_2(p):
    '''closed_exprsuite : LBRACE suite RBRACE'''
    #                          1     2      3
    print("closed_exprsuite : LBRACE suite RBRACE")
def p_closed_exprsuite_3(p):
    '''closed_exprsuite : COLON LBRACE suite RBRACE'''
    #                         1      2     3      4
    print("closed_exprsuite : COLON LBRACE suite RBRACE")

# ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' exprsuite)
def p_ifblock_1(p):
    '''ifblock : IF expression exprsuite ELSE exprsuite'''
    #             1          2         3    4         5
    print("ifblock : IF expression exprsuite ELSE exprsuite")
def p_ifblock_2(p):
    '''ifblock : IF expression exprsuite ifblock_star ELSE exprsuite'''
    #             1          2         3            4    5         6
    print("ifblock : IF expression exprsuite ifblock_star ELSE exprsuite")

def p_ifblock_star_1(p):
    '''ifblock_star : ELIF expression exprsuite'''
    #                    1          2         3
    print("ifblock_star : ELIF expression exprsuite")
def p_ifblock_star_2(p):
    '''ifblock_star : ifblock_star ELIF expression exprsuite'''
    #                            1    2          3         4
    print("ifblock_star : ifblock_star ELIF expression exprsuite")

# closed_ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' closed_exprsuite)
def p_closed_ifblock_1(p):
    '''closed_ifblock : IF expression exprsuite ELSE closed_exprsuite'''
    #                    1          2         3    4                5
    print("closed_ifblock : IF expression exprsuite ELSE closed_exprsuite")
def p_closed_ifblock_2(p):
    '''closed_ifblock : IF expression exprsuite closed_ifblock_star ELSE closed_exprsuite'''
    #                    1          2         3                   4    5                6
    print("closed_ifblock : IF expression exprsuite closed_ifblock_star ELSE closed_exprsuite")

def p_closed_ifblock_star_1(p):
    '''closed_ifblock_star : ELIF expression exprsuite'''
    #                           1          2         3
    print("closed_ifblock_star : ELIF expression exprsuite")
def p_closed_ifblock_star_2(p):
    '''closed_ifblock_star : closed_ifblock_star ELIF expression exprsuite'''
    #                                          1    2          3         4
    print("closed_ifblock_star : closed_ifblock_star ELIF expression exprsuite")

# or_test: and_test ('or' and_test)*
def p_or_test_1(p):
    '''or_test : and_test'''
    #                   1
    print("or_test : and_test")
def p_or_test_2(p):
    '''or_test : and_test or_test_star'''
    #                   1            2
    print("or_test : and_test or_test_star")

def p_or_test_star_1(p):
    '''or_test_star : OR and_test'''
    #                  1        2
    print("or_test_star : OR and_test")
def p_or_test_star_2(p):
    '''or_test_star : or_test_star OR and_test'''
    #                            1  2        3
    print("or_test_star : or_test_star OR and_test")

# and_test: not_test ('and' not_test)*
def p_and_test_1(p):
    '''and_test : not_test'''
    #                    1
    print("and_test : not_test")
def p_and_test_2(p):
    '''and_test : not_test and_test_star'''
    #                    1             2
    print("and_test : not_test and_test_star")

def p_and_test_star_1(p):
    '''and_test_star : AND not_test'''
    #                    1        2
    print("and_test_star : AND not_test")
def p_and_test_star_2(p):
    '''and_test_star : and_test_star AND not_test'''
    #                              1   2        3
    print("and_test_star : and_test_star AND not_test")

# not_test: 'not' not_test | comparison
def p_not_test_1(p):
    '''not_test : NOT not_test'''
    #               1        2
    print("not_test : NOT not_test")
def p_not_test_2(p):
    '''not_test : comparison'''
    #                      1
    print("not_test : comparison")

# comparison: arith_expr (comp_op arith_expr)*
def p_comparison_1(p):
    '''comparison : arith_expr'''
    #                        1
    print("comparison : arith_expr")
def p_comparison_2(p):
    '''comparison : arith_expr comparison_star'''
    #                        1               2
    print("comparison : arith_expr comparison_star")

def p_comparison_star_1(p):
    '''comparison_star : comp_op arith_expr'''
    #                          1          2
    print("comparison_star : comp_op arith_expr")
def p_comparison_star_2(p):
    '''comparison_star : comparison_star comp_op arith_expr'''
    #                                  1       2          3
    print("comparison_star : comparison_star comp_op arith_expr")

# comp_op: '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in'
def p_comp_op_1(p):
    '''comp_op : LESS'''
    #               1
    print("comp_op : LESS")
def p_comp_op_2(p):
    '''comp_op : GREATER'''
    #                  1
    print("comp_op : GREATER")
def p_comp_op_3(p):
    '''comp_op : EQEQUAL'''
    #                  1
    print("comp_op : EQEQUAL")
def p_comp_op_4(p):
    '''comp_op : GREATEREQUAL'''
    #                       1
    print("comp_op : GREATEREQUAL")
def p_comp_op_5(p):
    '''comp_op : LESSEQUAL'''
    #                    1
    print("comp_op : LESSEQUAL")
def p_comp_op_6(p):
    '''comp_op : NOTEQUAL'''
    #                   1
    print("comp_op : NOTEQUAL")
def p_comp_op_7(p):
    '''comp_op : IN'''
    #             1
    print("comp_op : IN")
def p_comp_op_8(p):
    '''comp_op : NOT IN'''
    #              1  2
    print("comp_op : NOT IN")

# arith_expr: term (('+' | '-') term)*
def p_arith_expr_1(p):
    '''arith_expr : term'''
    #                  1
    print("arith_expr : term")
def p_arith_expr_2(p):
    '''arith_expr : term arith_expr_star'''
    #                  1               2
    print("arith_expr : term arith_expr_star")

def p_arith_expr_star_1(p):
    '''arith_expr_star : PLUS term'''
    #                       1    2
    print("arith_expr_star : PLUS term")
def p_arith_expr_star_2(p):
    '''arith_expr_star : MINUS term'''
    #                        1    2
    print("arith_expr_star : MINUS term")
def p_arith_expr_star_3(p):
    '''arith_expr_star : arith_expr_star PLUS term'''
    #                                  1    2    3
    print("arith_expr_star : arith_expr_star PLUS term")
def p_arith_expr_star_4(p):
    '''arith_expr_star : arith_expr_star MINUS term'''
    #                                  1     2    3
    print("arith_expr_star : arith_expr_star MINUS term")

# term: factor (('*' | '/' | '%' | '//') factor)*
def p_term_1(p):
    '''term : factor'''
    #              1
    print("term : factor")
def p_term_2(p):
    '''term : factor term_star'''
    #              1         2
    print("term : factor term_star")

def p_term_star_1(p):
    '''term_star : STAR factor'''
    #                 1      2
    print("term_star : STAR factor")
def p_term_star_2(p):
    '''term_star : SLASH factor'''
    #                  1      2
    print("term_star : SLASH factor")
def p_term_star_3(p):
    '''term_star : PERCENT factor'''
    #                    1      2
    print("term_star : PERCENT factor")
def p_term_star_4(p):
    '''term_star : DOUBLESLASH factor'''
    #                        1      2
    print("term_star : DOUBLESLASH factor")
def p_term_star_5(p):
    '''term_star : term_star STAR factor'''
    #                      1    2      3
    print("term_star : term_star STAR factor")
def p_term_star_6(p):
    '''term_star : term_star SLASH factor'''
    #                      1     2      3
    print("term_star : term_star SLASH factor")
def p_term_star_7(p):
    '''term_star : term_star PERCENT factor'''
    #                      1       2      3
    print("term_star : term_star PERCENT factor")
def p_term_star_8(p):
    '''term_star : term_star DOUBLESLASH factor'''
    #                      1           2      3
    print("term_star : term_star DOUBLESLASH factor")

# factor: ('+' | '-') factor | power
def p_factor_1(p):
    '''factor : PLUS factor'''
    #              1      2
    print("factor : PLUS factor")
def p_factor_2(p):
    '''factor : MINUS factor'''
    #               1      2
    print("factor : MINUS factor")
def p_factor_3(p):
    '''factor : power'''
    #               1
    print("factor : power")

# power: atom trailer* ['**' factor]
def p_power_1(p):
    '''power : atom'''
    #             1
    print("power : atom")
def p_power_2(p):
    '''power : atom DOUBLESTAR factor'''
    #             1          2      3
    print("power : atom DOUBLESTAR factor")
def p_power_3(p):
    '''power : atom power_star'''
    #             1          2
    print("power : atom power_star")
def p_power_4(p):
    '''power : atom power_star DOUBLESTAR factor'''
    #             1          2          3      4
    print("power : atom power_star DOUBLESTAR factor")

def p_power_star_1(p):
    '''power_star : trailer'''
    #                     1
    print("power_star : trailer")
def p_power_star_2(p):
    '''power_star : power_star trailer'''
    #                        1       2
    print("power_star : power_star trailer")

# atom: ('(' [expression] ')'
#         | STRING
#         | IMAG_NUMBER
#         | FLOAT_NUMBER
#         | HEX_NUMBER
#         | OCT_NUMBER
#         | DEC_NUMBER
#         | ATARG
#         | NAME)
def p_atom_1(p):
    '''atom : LPAR RPAR'''
    #            1    2
    print("atom : LPAR RPAR")
def p_atom_2(p):
    '''atom : LPAR expression RPAR'''
    #            1          2    3
    print("atom : LPAR expression RPAR")
def p_atom_3(p):
    '''atom : STRING'''
    #              1
    print("atom : STRING")
def p_atom_4(p):
    '''atom : IMAG_NUMBER'''
    #                   1
    print("atom : IMAG_NUMBER")
def p_atom_5(p):
    '''atom : FLOAT_NUMBER'''
    #                    1
    print("atom : FLOAT_NUMBER")
def p_atom_6(p):
    '''atom : HEX_NUMBER'''
    #                  1
    print("atom : HEX_NUMBER")
def p_atom_7(p):
    '''atom : OCT_NUMBER'''
    #                  1
    print("atom : OCT_NUMBER")
def p_atom_8(p):
    '''atom : DEC_NUMBER'''
    #                  1
    print("atom : DEC_NUMBER")
def p_atom_9(p):
    '''atom : ATARG'''
    #             1
    print("atom : ATARG")
def p_atom_10(p):
    '''atom : NAME'''
    #            1
    print("atom : NAME")

# trailer: '(' (arglist | fcn1def) ')' | '[' subscriptlist ']' | '.' NAME
def p_trailer_1(p):
    '''trailer : LPAR arglist RPAR'''
    #               1       2    3
    print("trailer : LPAR arglist RPAR")
def p_trailer_2(p):
    '''trailer : LPAR fcn1def RPAR'''
    #               1       2    3
    print("trailer : LPAR fcn1def RPAR")
def p_trailer_3(p):
    '''trailer : LSQB subscriptlist RSQB'''
    #               1             2    3
    print("trailer : LSQB subscriptlist RSQB")
def p_trailer_4(p):
    '''trailer : DOT NAME'''
    #              1    2
    print("trailer : DOT NAME")

# subscriptlist: subscript (',' subscript)* [',']
def p_subscriptlist_1(p):
    '''subscriptlist : subscript'''
    #                          1
    print("subscriptlist : subscript")
def p_subscriptlist_2(p):
    '''subscriptlist : subscript COMMA'''
    #                          1     2
    print("subscriptlist : subscript COMMA")
def p_subscriptlist_3(p):
    '''subscriptlist : subscript subscriptlist_star'''
    #                          1                  2
    print("subscriptlist : subscript subscriptlist_star")
def p_subscriptlist_4(p):
    '''subscriptlist : subscript subscriptlist_star COMMA'''
    #                          1                  2     3
    print("subscriptlist : subscript subscriptlist_star COMMA")

def p_subscriptlist_star_1(p):
    '''subscriptlist_star : COMMA subscript'''
    #                           1         2
    print("subscriptlist_star : COMMA subscript")
def p_subscriptlist_star_2(p):
    '''subscriptlist_star : subscriptlist_star COMMA subscript'''
    #                                        1     2         3
    print("subscriptlist_star : subscriptlist_star COMMA subscript")

# subscript: expression | [expression] ':' [expression] [sliceop]
def p_subscript_1(p):
    '''subscript : expression'''
    #                       1
    print("subscript : expression")
def p_subscript_2(p):
    '''subscript : COLON'''
    #                  1
    print("subscript : COLON")
def p_subscript_3(p):
    '''subscript : COLON sliceop'''
    #                  1       2
    print("subscript : COLON sliceop")
def p_subscript_4(p):
    '''subscript : COLON expression'''
    #                  1          2
    print("subscript : COLON expression")
def p_subscript_5(p):
    '''subscript : COLON expression sliceop'''
    #                  1          2       3
    print("subscript : COLON expression sliceop")
def p_subscript_6(p):
    '''subscript : expression COLON'''
    #                       1     2
    print("subscript : expression COLON")
def p_subscript_7(p):
    '''subscript : expression COLON sliceop'''
    #                       1     2       3
    print("subscript : expression COLON sliceop")
def p_subscript_8(p):
    '''subscript : expression COLON expression'''
    #                       1     2          3
    print("subscript : expression COLON expression")
def p_subscript_9(p):
    '''subscript : expression COLON expression sliceop'''
    #                       1     2          3       4
    print("subscript : expression COLON expression sliceop")

# sliceop: ':' [expression]
def p_sliceop_1(p):
    '''sliceop : COLON'''
    #                1
    print("sliceop : COLON")
def p_sliceop_2(p):
    '''sliceop : COLON expression'''
    #                1          2
    print("sliceop : COLON expression")

# arglist: (argument ',')* (argument [','])
def p_arglist_1(p):
    '''arglist : argument'''
    #                   1
    print("arglist : argument")
def p_arglist_2(p):
    '''arglist : argument COMMA'''
    #                   1     2
    print("arglist : argument COMMA")
def p_arglist_3(p):
    '''arglist : arglist_star argument'''
    #                       1        2
    print("arglist : arglist_star argument")
def p_arglist_4(p):
    '''arglist : arglist_star argument COMMA'''
    #                       1        2     3
    print("arglist : arglist_star argument COMMA")

def p_arglist_star_1(p):
    '''arglist_star : argument COMMA'''
    #                        1     2
    print("arglist_star : argument COMMA")
def p_arglist_star_2(p):
    '''arglist_star : arglist_star argument COMMA'''
    #                            1        2     3
    print("arglist_star : arglist_star argument COMMA")

# argument: expression | NAME '=' expression
def p_argument_1(p):
    '''argument : expression'''
    #                      1
    print("argument : expression")
def p_argument_2(p):
    '''argument : NAME EQUAL expression'''
    #                1     2          3
    print("argument : NAME EQUAL expression")

def p_error(p):
    raise SyntaxError(p)

def parse(source, fileName="<unknown>"):
    lexer = lex.lex()
    parser = yacc.yacc()
    return parser.parse(source, lexer=lexer)


#!/usr/bin/env python
# generated at ('2016-10-06T14:33:23', 'femtocode.g actions.py parser.py') by "python femtocode.g actions.py parser.py"

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

def t_error(t):
    raise SyntaxError(t)

def t_comment(t):
    r"[ ]*\043[^\n]*"  # \043 is # ; otherwise PLY thinks it is a regex comment
    pass

t_ignore = " \t\f"

def inherit_lineno(p0, px, alt=True):
    if isinstance(px, dict):
        p0.lineno = px["lineno"]
        p0.col_offset = px["col_offset"]
    else:
        if alt and hasattr(px, "alt"):
            p0.lineno = px.alt["lineno"]
            p0.col_offset = px.alt["col_offset"]
        else:
            p0.lineno = px.lineno
            p0.col_offset = px.col_offset

def unwrap_left_associative(args, rule, alt=False):
    out = ast.BinOp(args[0], args[1], args[2], rule=rule)
    inherit_lineno(out, args[0])
    args = args[3:]
    while len(args) > 0:
        out = ast.BinOp(out, args[0], args[1], rule=rule)
        inherit_lineno(out, out.left)
        if alt:
            out.alt = {"lineno": out.lineno, "col_offset": out.col_offset}
            inherit_lineno(out, out.op)
        args = args[2:]
    return out

def unpack_trailer(atom, power_star):
    out = atom
    for trailer in power_star:
        if isinstance(trailer, ast.Call):
            trailer.func = out
            inherit_lineno(trailer, out)
            out = trailer
        elif isinstance(trailer, ast.Attribute):
            trailer.value = out
            inherit_lineno(trailer, out, alt=False)
            if hasattr(out, "alt"):
                trailer.alt = out.alt
            out = trailer
        elif isinstance(trailer, ast.Subscript):
            trailer.value = out
            inherit_lineno(trailer, out)
            out = trailer
        else:
            assert False
    return out


# body: ';'* suite
def p_body_1(p):
    '''body : suite'''
    #             1
    raise NotImplementedError
def p_body_2(p):
    '''body : body_star suite'''
    #                 1     2
    raise NotImplementedError

def p_body_star_1(p):
    '''body_star : SEMI'''
    #                 1
    raise NotImplementedError
def p_body_star_2(p):
    '''body_star : body_star SEMI'''
    #                      1    2
    raise NotImplementedError

# suite: (assignment ';'*)* expression ';'*
def p_suite_1(p):
    '''suite : expression'''
    #                   1
    raise NotImplementedError
def p_suite_2(p):
    '''suite : expression suite_star'''
    #                   1          2
    raise NotImplementedError
def p_suite_3(p):
    '''suite : suite_star2 expression'''
    #                    1          2
    raise NotImplementedError
def p_suite_4(p):
    '''suite : suite_star2 expression suite_star3'''
    #                    1          2           3
    raise NotImplementedError

def p_suite_star_1(p):
    '''suite_star : SEMI'''
    #                  1
    raise NotImplementedError
def p_suite_star_2(p):
    '''suite_star : suite_star SEMI'''
    #                        1    2
    raise NotImplementedError

def p_suite_star3_1(p):
    '''suite_star3 : SEMI'''
    #                   1
    raise NotImplementedError
def p_suite_star3_2(p):
    '''suite_star3 : suite_star3 SEMI'''
    #                          1    2
    raise NotImplementedError

def p_suite_star2_1(p):
    '''suite_star2 : assignment'''
    #                         1
    raise NotImplementedError
def p_suite_star2_2(p):
    '''suite_star2 : assignment suite_star2_star'''
    #                         1                2
    raise NotImplementedError
def p_suite_star2_3(p):
    '''suite_star2 : suite_star2 assignment'''
    #                          1          2
    raise NotImplementedError
def p_suite_star2_4(p):
    '''suite_star2 : suite_star2 assignment suite_star2_star'''
    #                          1          2                3
    raise NotImplementedError

def p_suite_star2_star_1(p):
    '''suite_star2_star : SEMI'''
    #                        1
    raise NotImplementedError
def p_suite_star2_star_2(p):
    '''suite_star2_star : suite_star2_star SEMI'''
    #                                    1    2
    raise NotImplementedError

# lvalues: (NAME ',')* NAME [',']     // source of "WARNING: 1 shift/reduce conflict" but works
def p_lvalues_1(p):
    '''lvalues : NAME'''
    #               1
    raise NotImplementedError
def p_lvalues_2(p):
    '''lvalues : NAME COMMA'''
    #               1     2
    raise NotImplementedError
def p_lvalues_3(p):
    '''lvalues : lvalues_star NAME'''
    #                       1    2
    raise NotImplementedError
def p_lvalues_4(p):
    '''lvalues : lvalues_star NAME COMMA'''
    #                       1    2     3
    raise NotImplementedError

def p_lvalues_star_1(p):
    '''lvalues_star : NAME COMMA'''
    #                    1     2
    raise NotImplementedError
def p_lvalues_star_2(p):
    '''lvalues_star : lvalues_star NAME COMMA'''
    #                            1    2     3
    raise NotImplementedError

# assignment: lvalues '=' closed_expression | fcnndef
def p_assignment_1(p):
    '''assignment : lvalues EQUAL closed_expression'''
    #                     1     2                 3
    raise NotImplementedError
def p_assignment_2(p):
    '''assignment : fcnndef'''
    #                     1
    raise NotImplementedError

# fcnndef: 'def' NAME '(' paramlist ')' closed_exprsuite
def p_fcnndef(p):
    '''fcnndef : DEF NAME LPAR paramlist RPAR closed_exprsuite'''
    #              1    2    3         4    5                6
    raise NotImplementedError

# expression: ifblock | fcndef | or_test
def p_expression_1(p):
    '''expression : ifblock'''
    #                     1
    raise NotImplementedError
def p_expression_2(p):
    '''expression : fcndef'''
    #                    1
    raise NotImplementedError
def p_expression_3(p):
    '''expression : or_test'''
    #                     1
    raise NotImplementedError

# closed_expression: closed_ifblock | fcndef | or_test ';'
def p_closed_expression_1(p):
    '''closed_expression : closed_ifblock'''
    #                                   1
    raise NotImplementedError
def p_closed_expression_2(p):
    '''closed_expression : fcndef'''
    #                           1
    raise NotImplementedError
def p_closed_expression_3(p):
    '''closed_expression : or_test SEMI'''
    #                            1    2
    raise NotImplementedError

# fcndef: '{' paramlist '=>' suite '}'
def p_fcndef(p):
    '''fcndef : LBRACE paramlist RIGHTARROW suite RBRACE'''
    #                1         2          3     4      5
    raise NotImplementedError

# fcn1def: parameter '=>' (expression | '{' suite '}')
def p_fcn1def_1(p):
    '''fcn1def : parameter RIGHTARROW expression'''
    #                    1          2          3
    raise NotImplementedError
def p_fcn1def_2(p):
    '''fcn1def : parameter RIGHTARROW LBRACE suite RBRACE'''
    #                    1          2      3     4      5
    raise NotImplementedError

# paramlist: (parameter ',')* (parameter [','])
def p_paramlist_1(p):
    '''paramlist : parameter'''
    #                      1
    raise NotImplementedError
def p_paramlist_2(p):
    '''paramlist : parameter COMMA'''
    #                      1     2
    raise NotImplementedError
def p_paramlist_3(p):
    '''paramlist : paramlist_star parameter'''
    #                           1         2
    raise NotImplementedError
def p_paramlist_4(p):
    '''paramlist : paramlist_star parameter COMMA'''
    #                           1         2     3
    raise NotImplementedError

def p_paramlist_star_1(p):
    '''paramlist_star : parameter COMMA'''
    #                           1     2
    raise NotImplementedError
def p_paramlist_star_2(p):
    '''paramlist_star : paramlist_star parameter COMMA'''
    #                                1         2     3
    raise NotImplementedError

# parameter: NAME
def p_parameter(p):
    '''parameter : NAME'''
    #                 1
    raise NotImplementedError

# exprsuite: (':' expression | [':'] '{' suite '}')
def p_exprsuite_1(p):
    '''exprsuite : COLON expression'''
    #                  1          2
    raise NotImplementedError
def p_exprsuite_2(p):
    '''exprsuite : LBRACE suite RBRACE'''
    #                   1     2      3
    raise NotImplementedError
def p_exprsuite_3(p):
    '''exprsuite : COLON LBRACE suite RBRACE'''
    #                  1      2     3      4
    raise NotImplementedError

# closed_exprsuite: (':' closed_expression | [':'] '{' suite '}')
def p_closed_exprsuite_1(p):
    '''closed_exprsuite : COLON closed_expression'''
    #                         1                 2
    raise NotImplementedError
def p_closed_exprsuite_2(p):
    '''closed_exprsuite : LBRACE suite RBRACE'''
    #                          1     2      3
    raise NotImplementedError
def p_closed_exprsuite_3(p):
    '''closed_exprsuite : COLON LBRACE suite RBRACE'''
    #                         1      2     3      4
    raise NotImplementedError

# ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' exprsuite)
def p_ifblock_1(p):
    '''ifblock : IF expression exprsuite ELSE exprsuite'''
    #             1          2         3    4         5
    raise NotImplementedError
def p_ifblock_2(p):
    '''ifblock : IF expression exprsuite ifblock_star ELSE exprsuite'''
    #             1          2         3            4    5         6
    raise NotImplementedError

def p_ifblock_star_1(p):
    '''ifblock_star : ELIF expression exprsuite'''
    #                    1          2         3
    raise NotImplementedError
def p_ifblock_star_2(p):
    '''ifblock_star : ifblock_star ELIF expression exprsuite'''
    #                            1    2          3         4
    raise NotImplementedError

# closed_ifblock: ('if' expression exprsuite ('elif' expression exprsuite)* 'else' closed_exprsuite)
def p_closed_ifblock_1(p):
    '''closed_ifblock : IF expression exprsuite ELSE closed_exprsuite'''
    #                    1          2         3    4                5
    raise NotImplementedError
def p_closed_ifblock_2(p):
    '''closed_ifblock : IF expression exprsuite closed_ifblock_star ELSE closed_exprsuite'''
    #                    1          2         3                   4    5                6
    raise NotImplementedError

def p_closed_ifblock_star_1(p):
    '''closed_ifblock_star : ELIF expression exprsuite'''
    #                           1          2         3
    raise NotImplementedError
def p_closed_ifblock_star_2(p):
    '''closed_ifblock_star : closed_ifblock_star ELIF expression exprsuite'''
    #                                          1    2          3         4
    raise NotImplementedError

# or_test: and_test ('or' and_test)*
def p_or_test_1(p):
    '''or_test : and_test'''
    #                   1
    p[0] = p[1]
def p_or_test_2(p):
    '''or_test : and_test or_test_star'''
    #                   1            2
    theor = ast.Or(rule=inspect.currentframe().f_code.co_name)
    inherit_lineno(theor, p[2][0])
    p[0] = ast.BoolOp(theor, [p[1]] + p[2], rule=inspect.currentframe().f_code.co_name)
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
    theand = ast.And(rule=inspect.currentframe().f_code.co_name)
    inherit_lineno(theand, p[2][0])
    p[0] = ast.BoolOp(theand, [p[1]] + p[2], rule=inspect.currentframe().f_code.co_name)
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
    thenot = ast.Not(rule=inspect.currentframe().f_code.co_name)
    inherit_lineno(thenot, p[2])
    p[0] = ast.UnaryOp(thenot, p[2], rule=inspect.currentframe().f_code.co_name, **p[1][1])
def p_not_test_2(p):
    '''not_test : comparison'''
    #                      1
    p[0] = p[1]

# comparison: arith_expr (comp_op arith_expr)*
def p_comparison_1(p):
    '''comparison : arith_expr'''
    #                        1
    raise NotImplementedError
def p_comparison_2(p):
    '''comparison : arith_expr comparison_star'''
    #                        1               2
    raise NotImplementedError

def p_comparison_star_1(p):
    '''comparison_star : comp_op arith_expr'''
    #                          1          2
    raise NotImplementedError
def p_comparison_star_2(p):
    '''comparison_star : comparison_star comp_op arith_expr'''
    #                                  1       2          3
    raise NotImplementedError

# comp_op: '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in'
def p_comp_op_1(p):
    '''comp_op : LESS'''
    #               1
    p[0] = ast.Lt(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_2(p):
    '''comp_op : GREATER'''
    #                  1
    p[0] = ast.Gt(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_3(p):
    '''comp_op : EQEQUAL'''
    #                  1
    p[0] = ast.Eq(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_4(p):
    '''comp_op : GREATEREQUAL'''
    #                       1
    p[0] = ast.GtE(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_5(p):
    '''comp_op : LESSEQUAL'''
    #                    1
    p[0] = ast.LtE(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_6(p):
    '''comp_op : NOTEQUAL'''
    #                   1
    p[0] = ast.NotEq(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_7(p):
    '''comp_op : IN'''
    #             1
    p[0] = ast.In(rule=inspect.currentframe().f_code.co_name)
def p_comp_op_8(p):
    '''comp_op : NOT IN'''
    #              1  2
    p[0] = ast.NotIn(rule=inspect.currentframe().f_code.co_name)

# arith_expr: term (('+' | '-') term)*
def p_arith_expr_1(p):
    '''arith_expr : term'''
    #                  1
    p[0] = p[1]
def p_arith_expr_2(p):
    '''arith_expr : term arith_expr_star'''
    #                  1               2
    p[0] = unwrap_left_associative([p[1]] + p[2], rule=inspect.currentframe().f_code.co_name, alt=len(p[2]) > 2)

def p_arith_expr_star_1(p):
    '''arith_expr_star : PLUS term'''
    #                       1    2
    p[0] = [ast.Add(rule=inspect.currentframe().f_code.co_name, **p[1][1]), p[2]]
def p_arith_expr_star_2(p):
    '''arith_expr_star : MINUS term'''
    #                        1    2
    p[0] = [ast.Sub(rule=inspect.currentframe().f_code.co_name, **p[1][1]), p[2]]
def p_arith_expr_star_3(p):
    '''arith_expr_star : arith_expr_star PLUS term'''
    #                                  1    2    3
    p[0] = p[1] + [ast.Add(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3]]
def p_arith_expr_star_4(p):
    '''arith_expr_star : arith_expr_star MINUS term'''
    #                                  1     2    3
    p[0] = p[1] + [ast.Sub(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3]]

# term: factor (('*' | '/' | '%' | '//') factor)*
def p_term_1(p):
    '''term : factor'''
    #              1
    p[0] = p[1]
def p_term_2(p):
    '''term : factor term_star'''
    #              1         2
    p[0] = unwrap_left_associative([p[1]] + p[2], rule=inspect.currentframe().f_code.co_name, alt=len(p[2]) > 2)

def p_term_star_1(p):
    '''term_star : STAR factor'''
    #                 1      2
    p[0] = [ast.Mult(rule=inspect.currentframe().f_code.co_name, **p[1][1]), p[2]]
def p_term_star_2(p):
    '''term_star : SLASH factor'''
    #                  1      2
    p[0] = [ast.Div(rule=inspect.currentframe().f_code.co_name, **p[1][1]), p[2]]
def p_term_star_3(p):
    '''term_star : PERCENT factor'''
    #                    1      2
    p[0] = [ast.Mod(rule=inspect.currentframe().f_code.co_name, **p[1][1]), p[2]]
def p_term_star_4(p):
    '''term_star : DOUBLESLASH factor'''
    #                        1      2
    p[0] = [ast.FloorDiv(rule=inspect.currentframe().f_code.co_name, **p[1][1]), p[2]]
def p_term_star_5(p):
    '''term_star : term_star STAR factor'''
    #                      1    2      3
    p[0] = p[1] + [ast.Mult(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3]]
def p_term_star_6(p):
    '''term_star : term_star SLASH factor'''
    #                      1     2      3
    p[0] = p[1] + [ast.Div(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3]]
def p_term_star_7(p):
    '''term_star : term_star PERCENT factor'''
    #                      1       2      3
    p[0] = p[1] + [ast.Mod(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3]]
def p_term_star_8(p):
    '''term_star : term_star DOUBLESLASH factor'''
    #                      1           2      3
    p[0] = p[1] + [ast.FloorDiv(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3]]

# factor: ('+' | '-') factor | power
def p_factor_1(p):
    '''factor : PLUS factor'''
    #              1      2
    op = ast.UAdd(rule=inspect.currentframe().f_code.co_name, **p[1][1])
    p[0] = ast.UnaryOp(op, p[2], rule=inspect.currentframe().f_code.co_name)
    inherit_lineno(p[0], op)
def p_factor_2(p):
    '''factor : MINUS factor'''
    #               1      2
    if isinstance(p[2], ast.Num) and not hasattr(p[2], "unary"):
        p[2].n *= -1
        p[0] = p[2]
        p[0].unary = True
        inherit_lineno(p[0], p[1][1])
    else:
        op = ast.USub(rule=inspect.currentframe().f_code.co_name, **p[1][1])
        p[0] = ast.UnaryOp(op, p[2], rule=inspect.currentframe().f_code.co_name)
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
    p[0] = ast.BinOp(p[1], ast.Pow(rule=inspect.currentframe().f_code.co_name, **p[2][1]), p[3], rule=inspect.currentframe().f_code.co_name)
    inherit_lineno(p[0], p[1])
def p_power_3(p):
    '''power : atom power_star'''
    #             1          2
    p[0] = unpack_trailer(p[1], p[2])
def p_power_4(p):
    '''power : atom power_star DOUBLESTAR factor'''
    #             1          2          3      4
    p[0] = ast.BinOp(unpack_trailer(p[1], p[2]), ast.Pow(rule=inspect.currentframe().f_code.co_name, **p[3][1]), p[4], rule=inspect.currentframe().f_code.co_name)
    inherit_lineno(p[0], p[1])

def p_power_star_1(p):
    '''power_star : trailer'''
    #                     1
    p[0] = [p[1]]
def p_power_star_2(p):
    '''power_star : power_star trailer'''
    #                        1       2
    p[0] = p[1] + [p[2]]

# atom: ('(' [expression] ')'
#         | fcndef '(' arglist ')'    // source of "WARNING: 1 shift/reduce conflict" but works
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
    raise NotImplementedError
def p_atom_2(p):
    '''atom : LPAR expression RPAR'''
    #            1          2    3
    raise NotImplementedError
def p_atom_3(p):
    '''atom : fcndef LPAR arglist RPAR'''
    #              1    2       3    4
    raise NotImplementedError
def p_atom_4(p):
    '''atom : STRING'''
    #              1
    raise NotImplementedError
def p_atom_5(p):
    '''atom : IMAG_NUMBER'''
    #                   1
    raise NotImplementedError
def p_atom_6(p):
    '''atom : FLOAT_NUMBER'''
    #                    1
    raise NotImplementedError
def p_atom_7(p):
    '''atom : HEX_NUMBER'''
    #                  1
    raise NotImplementedError
def p_atom_8(p):
    '''atom : OCT_NUMBER'''
    #                  1
    raise NotImplementedError
def p_atom_9(p):
    '''atom : DEC_NUMBER'''
    #                  1
    raise NotImplementedError
def p_atom_10(p):
    '''atom : ATARG'''
    #             1
    raise NotImplementedError
def p_atom_11(p):
    '''atom : NAME'''
    #            1
    raise NotImplementedError

# trailer: '(' arglist ')' | '[' subscriptlist ']' | '.' NAME
def p_trailer_1(p):
    '''trailer : LPAR arglist RPAR'''
    #               1       2    3
    p[0] = p[2]
def p_trailer_2(p):
    '''trailer : LSQB subscriptlist RSQB'''
    #               1             2    3
    p[0] = ast.Subscript(None, p[2], ast.Load(), rule=inspect.currentframe().f_code.co_name)
def p_trailer_3(p):
    '''trailer : DOT NAME'''
    #              1    2
    p[0] = ast.Attribute(None, p[2][0], ast.Load(), rule=inspect.currentframe().f_code.co_name)

# subscriptlist: subscript (',' subscript)* [',']
def p_subscriptlist_1(p):
    '''subscriptlist : subscript'''
    #                          1
    p[0] = p[1]
def p_subscriptlist_2(p):
    '''subscriptlist : subscript COMMA'''
    #                          1     2
    if isinstance(p[1], ast.Index):
        tup = ast.Tuple([p[1].value], ast.Load(), rule=inspect.currentframe().f_code.co_name, paren=False)
        inherit_lineno(tup, p[1].value)
        p[0] = ast.Index(tup, rule=inspect.currentframe().f_code.co_name)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ast.ExtSlice([p[1]], rule=inspect.currentframe().f_code.co_name)
        inherit_lineno(p[0], p[1])
def p_subscriptlist_3(p):
    '''subscriptlist : subscript subscriptlist_star'''
    #                          1                  2
    args = [p[1]] + p[2]
    if all(isinstance(x, ast.Index) for x in args):
        tup = ast.Tuple([x.value for x in args], ast.Load(), rule=inspect.currentframe().f_code.co_name, paren=False)
        inherit_lineno(tup, args[0].value)
        p[0] = ast.Index(tup, rule=inspect.currentframe().f_code.co_name)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ast.ExtSlice(args, rule=inspect.currentframe().f_code.co_name)
        inherit_lineno(p[0], p[1])
def p_subscriptlist_4(p):
    '''subscriptlist : subscript subscriptlist_star COMMA'''
    #                          1                  2     3
    args = [p[1]] + p[2]
    if all(isinstance(x, ast.Index) for x in args):
        tup = ast.Tuple([x.value for x in args], ast.Load(), rule=inspect.currentframe().f_code.co_name, paren=False)
        inherit_lineno(tup, args[0].value)
        p[0] = ast.Index(tup, rule=inspect.currentframe().f_code.co_name)
        inherit_lineno(p[0], tup)
    else:
        p[0] = ast.ExtSlice(args, rule=inspect.currentframe().f_code.co_name)
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
    raise NotImplementedError
def p_subscript_2(p):
    '''subscript : COLON'''
    #                  1
    p[0] = ast.Slice(None, None, None, rule=inspect.currentframe().f_code.co_name, **p[1][1])
def p_subscript_3(p):
    '''subscript : COLON sliceop'''
    #                  1       2
    p[0] = ast.Slice(None, None, p[2], rule=inspect.currentframe().f_code.co_name, **p[1][1])
def p_subscript_4(p):
    '''subscript : COLON expression'''
    #                  1          2
    raise NotImplementedError
def p_subscript_5(p):
    '''subscript : COLON expression sliceop'''
    #                  1          2       3
    raise NotImplementedError
def p_subscript_6(p):
    '''subscript : expression COLON'''
    #                       1     2
    raise NotImplementedError
def p_subscript_7(p):
    '''subscript : expression COLON sliceop'''
    #                       1     2       3
    raise NotImplementedError
def p_subscript_8(p):
    '''subscript : expression COLON expression'''
    #                       1     2          3
    raise NotImplementedError
def p_subscript_9(p):
    '''subscript : expression COLON expression sliceop'''
    #                       1     2          3       4
    raise NotImplementedError

# sliceop: ':' [expression]
def p_sliceop_1(p):
    '''sliceop : COLON'''
    #                1
    p[0] = ast.Name("None", ast.Load(), rule=inspect.currentframe().f_code.co_name, **p[1][1])
def p_sliceop_2(p):
    '''sliceop : COLON expression'''
    #                1          2
    raise NotImplementedError

# arglist: ((argument ',')* (argument [','])) | fcn1def
def p_arglist_1(p):
    '''arglist : argument'''
    #                   1
    raise NotImplementedError
def p_arglist_2(p):
    '''arglist : argument COMMA'''
    #                   1     2
    raise NotImplementedError
def p_arglist_3(p):
    '''arglist : arglist_star argument'''
    #                       1        2
    raise NotImplementedError
def p_arglist_4(p):
    '''arglist : arglist_star argument COMMA'''
    #                       1        2     3
    raise NotImplementedError
def p_arglist_5(p):
    '''arglist : fcn1def'''
    #                  1
    raise NotImplementedError

def p_arglist_star_1(p):
    '''arglist_star : argument COMMA'''
    #                        1     2
    raise NotImplementedError
def p_arglist_star_2(p):
    '''arglist_star : arglist_star argument COMMA'''
    #                            1        2     3
    raise NotImplementedError

# argument: expression | NAME '=' expression
def p_argument_1(p):
    '''argument : expression'''
    #                      1
    raise NotImplementedError
def p_argument_2(p):
    '''argument : NAME EQUAL expression'''
    #                1     2          3
    raise NotImplementedError

def p_error(p):
    raise SyntaxError(p)

def parse(source, fileName="<unknown>"):
    lexer = lex.lex()
    parser = yacc.yacc()
    return parser.parse(source, lexer=lexer)


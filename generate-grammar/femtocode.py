#!/usr/bin/env python
# generated at NOW by "python femtocode.g femtocode.py"

import re
import ast

from ply import lex
from ply import yacc

tokens = []

def t_STRING(t):
    r'([uUbB]?[rR]?\'[^\\n\'\\\\]*(?:\\\\.[^\\n\'\\\\]*)*\'|[uUbB]?[rR]?"[^\\n"\\\\]*(?:\\\\.[^\\n"\\\\]*)*")'
    return t
tokens.append("STRING")

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

def t_NAME(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    return t
tokens.append("NAME")

reserved = {
  'and': 'AND',
  'is': 'IS',
  'else': 'ELSE',
  'in': 'IN',
  'not': 'NOT',
  'if': 'IF',
  'or': 'OR',
  'def': 'DEF',
  }

tokens.extend(['AT', 'VBAR', 'CIRCUMFLEX', 'TILDE', 'LSQB', 'DOT', 'RSQB', 'LBRACE', 'BANG', 'BACKQUOTE', 'PERCENT', 'AMPER', 'RPAR', 'LPAR', 'PLUS', 'STAR', 'MINUS', 'COMMA', 'SLASH', 'LESS', 'RBRACE', 'SEMI', 'COLON', 'EQUAL', 'GREATER'])

literals = ['@', '|', '^', '~', '[', '.', ']', '{', '!', '`', '%', '&', ')', '(', '+', '*', '-', ',', '/', '<', '}', ';', ':', '=', '>']

def t_AT(t):
    r"\@"
    return t

def t_VBAR(t):
    r"\|"
    return t

def t_CIRCUMFLEX(t):
    r"\^"
    return t

def t_TILDE(t):
    r"\~"
    return t

def t_LSQB(t):
    r"\["
    return t

def t_DOT(t):
    r"\."
    return t

def t_RSQB(t):
    r"\]"
    return t

def t_LBRACE(t):
    r"\{"
    return t

def t_BANG(t):
    r"\!"
    return t

def t_BACKQUOTE(t):
    r"\`"
    return t

def t_PERCENT(t):
    r"\%"
    return t

def t_AMPER(t):
    r"\&"
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

def t_error(t):
    raise SyntaxError(t)

def t_comment(t):
    r"[ ]*\043[^\n]*"  # \043 is # ; otherwise PLY thinks it is a regex comment
    pass

t_ignore = " \t\f\n"


# atom: NAME | HEX_NUMBER | OCT_NUMBER | DEC_NUMBER | FLOAT_NUMBER | STRING
def p_atom_1(p):
    '''atom : NAME'''
    #            1
    print("atom : NAME")
def p_atom_2(p):
    '''atom : HEX_NUMBER'''
    #                  1
    print("atom : HEX_NUMBER")
def p_atom_3(p):
    '''atom : OCT_NUMBER'''
    #                  1
    print("atom : OCT_NUMBER")
def p_atom_4(p):
    '''atom : DEC_NUMBER'''
    #                  1
    print("atom : DEC_NUMBER")
def p_atom_5(p):
    '''atom : FLOAT_NUMBER'''
    #                    1
    print("atom : FLOAT_NUMBER")
def p_atom_6(p):
    '''atom : STRING'''
    #              1
    print("atom : STRING")

def p_error(p):
    raise SyntaxError(p)

def parse(source, fileName="<unknown>"):
    lexer = lex.lex()
    parser = yacc.yacc()
    return parser.parse(source + "\n", lexer=lexer)


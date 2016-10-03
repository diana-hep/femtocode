#!/usr/bin/env python

# Written by Andrew Dalke
# Copyright (c) 2008 by Dalke Scientific, AB
# Modified by Jim Pivarski, 2016
# 
# (This is the MIT License with the serial numbers scratched off and my
# name written in in crayon.  I would prefer "share and enjoy" but
# apparently that isn't a legally acceptable.)
# 
# Copyright (c) 2008 Andrew Dalke <dalke@dalkescientific.com>
# Dalke Scientific Software, AB
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""This program converts a grammar.g file into a PLY grammar.

The grammar.g file is pretty simple but not designed for LALR(1) and
similar parsers. This program tweaks the grammar slightly and
flattens the results to a more usable form. It might prove useful for
other parsers. (Yes, it did.)
"""

import datetime
import importlib
import itertools
import re
import sys
import time

from ply import lex, yacc

inputGrammar, outputPLY, = sys.argv[1:]

literal_to_name = {
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "in": "IN",
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "def": "DEF",

    # "\n": "NL",

    "==": "EQEQUAL",       # 2-character tokens first
    "!=": "NOTEQUAL",
    "<=": "LESSEQUAL",
    ">=": "GREATEREQUAL",
    "**": "DOUBLESTAR",
    "//": "DOUBLESLASH",
    "=>": "RIGHTARROW",

    ":": "COLON",          # single-character literals
    ",": "COMMA",
    ";": "SEMI",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "<": "LESS",
    ">": "GREATER",
    "=": "EQUAL",
    ".": "DOT",
    "%": "PERCENT",

    "(": "LPAR",           # braces
    ")": "RPAR",
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LSQB",
    "]": "RSQB"}

tokens = ("LEXER_NAME", "PARSER_NAME", "STRING", "NL", "LPAR", "RPAR", "COLON")

def t_comment(t):
    r"\#.*"
    pass

t_ignore = " \t"

def t_NL(t):
    r"\n"
    t.value = t.lexer.lineno
    t.lexer.lineno += 1
    if getattr(t.lexer, "paren_depth", 0) == 0:
        return t

def t_word(t):
    r"[a-zA-Z_0-9]+"
    if t.value == t.value.upper():
        t.type = "LEXER_NAME"
        return t
    if t.value == t.value.lower():
        t.type = "PARSER_NAME"
        return t
    raise AssertionError("Unknown word: %r" % t.value)

t_STRING = r"'[^']+'"

def t_LPAR(t):
    r"\("
    t.lexer.paren_depth = getattr(t.lexer, "paren_depth", 0)+1
    return t

def t_RPAR(t):
    r"\)"
    t.lexer.paren_depth = getattr(t.lexer, "paren_depth", 0)-1
    assert t.lexer.paren_depth >= 0
    return t

def t_COLON(t):
    r":"
    t.value = t.lexer.lineno
    return t

literals = ('[', ']', '|', '+', '*')

def t_error(t):
    raise AssertionError(t)

lexer = lex.lex()

class Definition(object):
    def __init__(self, name, expr, first_line, last_line):
        self.name = name
        self.expr = expr
        self.first_line = first_line
        self.last_line = last_line
    def __repr__(self):
        return "Definition(%r, %r, %r, %r)" % (
            self.name, self.expr, self.first_line, self.last_line)

class Star(object):
    def __init__(self, child):
        self.child = child
    def __repr__(self):
        return "Star(%r)" % (self.child,)

class Plus(object):
    def __init__(self, child):
        self.child = child
    def __repr__(self):
        return "Plus(%r)" % (self.child,)

class Opt(object):
    def __init__(self, child):
        self.child = child
    def __repr__(self):
        return "Opt(%r)" % (self.child,)

class Or(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return "Or(%r, %r)" % (self.left, self.right)

class Seq(object):
    def __init__(self, first, next):
        self.first = first
        self.next = next
    def __repr__(self):
        return "Seq(%r, %r)" % (self.first, self.next)

def p_datafile1(p):
    """datafile : definition
                | datafile definition"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_datafile(p):
    """datafile : NL
                | datafile NL"""
    if len(p) == 3:
        p[0] = p[1]
    else:
        p[0] = []
            
def p_definition(p):
    """definition : PARSER_NAME COLON expr NL"""
    p[0] = Definition(p[1], p[3], p[2], p[4])

def p_expr(p):
    """expr : sequential_terms
            | expr '|' sequential_terms"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Or(p[1], p[3])

def p_sequential_terms(p):
    """sequential_terms : term
                        | sequential_terms term"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Seq(p[1], p[2])

def p_term(p):
    """term : element '*'
             | element '+'
             | element
             """
    if len(p) == 3:
        if p[2] == "+":
            p[0] = Plus(p[1])
        elif p[2] == "*":
            p[0] = Star(p[1])
        else:
            raise AssertionError(p[2])
    else:
        p[0] = p[1] # no repeat

def p_element(p):
    """element : '[' expr ']'
               | LPAR expr RPAR
               | STRING
               | LEXER_NAME
               | PARSER_NAME"""
    if len(p) == 4:
        if p[1] == '[':
            p[0] = Opt(p[2])
        else:
            p[0] = p[2] # no repeat
    elif p[1].startswith("'"):
        # Quoted string; turn into a token name
        literal = p[1][1:-1]
        p[0] = literal_to_name[literal]
    else:
        p[0] = p[1]

def p_error(p):
    raise AssertionError(p)

yacc.yacc(debug=False, write_tables=False)

grammar_text = open(inputGrammar).read()

definition_list = yacc.parse(grammar_text)

def add_flattened_definition(name, flat_expr):
    print name, ":", flat_expr

_seen_names = set()
def new_name(name):
    if name in _seen_names:
        for i in itertools.count(2):
            name2 = name + str(i)
            if name2 not in _seen_names:
                break
        name = name2
    _seen_names.add(name)
    return name

def flatten(name, expr, need_list):
    if isinstance(expr, Seq):
        for first_terms in flatten(name, expr.first, need_list):
            for next_terms in flatten(name, expr.next, need_list):
                yield first_terms + next_terms

    elif isinstance(expr, Or):
        for left_terms in flatten(name, expr.left, need_list):
            yield left_terms
        for right_terms in flatten(name, expr.right, need_list):
            yield right_terms

    elif isinstance(expr, Star):
        yield []
        child_name = new_name(name + "_star")
        yield [child_name]
        need_list.append( (child_name, expr.child) )

    elif isinstance(expr, Plus):
        child_name = new_name(name + "_plus")
        yield [child_name]
        need_list.append( (child_name, expr.child) )
    
    elif isinstance(expr, Opt):
        yield []
        for term in flatten(name, expr.child, need_list):
            yield term

    elif isinstance(expr, str):
        yield [expr]

    else:
        raise AssertionError(expr)
        
f = open(outputPLY, "w")
def W(s):
    f.write(s + "\n")

W('''#!/usr/bin/env python
# generated at %s by "python %s"

import re
import ast

from ply import lex
from ply import yacc

''' % ("NOW", " ".join(sys.argv[1:])))  # (datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S'), " ".join(sys.argv[1:]))

W("reserved = {\n%s  }\n" % "".join("  '%s': '%s',\n" % (literal, name) for literal, name in literal_to_name.items() if literal.isalpha()))

W("tokens = [%s]\n" % ", ".join("'%s'" % name for literal, name in literal_to_name.items() if literal.isalpha()))

W('''def t_STRING(t):
    r'([uUbB]?[rR]?\\'[^\\\\n\\'\\\\\\\\]*(?:\\\\\\\\.[^\\\\n\\'\\\\\\\\]*)*\\'|[uUbB]?[rR]?"[^\\\\n"\\\\\\\\]*(?:\\\\\\\\.[^\\\\n"\\\\\\\\]*)*")'
    return t
tokens.append("STRING")

def t_IMAG_NUMBER(t):
    r"(\\d+[jJ]|((\\d+\\.\\d*|\\.\\d+)([eE][-+]?\\d+)?|\\d+[eE][-+]?\\d+)[jJ])"
    return t
tokens.append("IMAG_NUMBER")

def t_FLOAT_NUMBER(t):
    r"((\\d+\\.\\d*|\\.\\d+)([eE][-+]?\\d+)?|\\d+[eE][-+]?\\d+)"
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
''')

W("tokens.extend([%s])\n" % ", ".join("'%s'" % name for literal, name in literal_to_name.items() if not literal.isalpha()))

W("literals = [%s]\n" % ", ".join("'%s'" % literal for literal, name in literal_to_name.items() if not literal.isalpha() and len(literal) == 1 and literal != "\n"))

for literal, name in literal_to_name.items():
    if not literal.isalpha() and len(literal) == 2:
        W('''def t_%s(t):
    r"%s"
    return t
''' % (name, re.escape(literal)))

for literal, name in literal_to_name.items():
    if not literal.isalpha() and len(literal) == 1 and literal != "\n":
        W('''def t_%s(t):
    r"%s"
    return t
''' % (name, re.escape(literal)))

W('''def t_NL(t):
    r"\\n"
    return t
''')

W('''def t_error(t):
    raise SyntaxError(t)
''')
W('''def t_comment(t):
    r"[ ]*\\043[^\\n]*"  # \\043 is # ; otherwise PLY thinks it is a regex comment
    pass
''')
W('''t_ignore = " \\t\\f\\n"
''')

def numbers(s):
    return " ".join(("%" + str(len(x)) + "d") % (i+1) for i, x in enumerate(s.split()))

def format_function(name, rules):
    if len(rules) == 1:
        W("def p_%s(p):" % name)
        W("    '''%s : %s'''" % (name, rules[0]))
        W("    #  %s   %s" % (" " * len(name), numbers(rules[0])))
        r = "%s : %s" % (name, rules[0])
        # if r in actions:
        #     W(actions[r])
        # else:
        # W("    raise NotImplementedError")
        W("    print(\"%s\")" % r)
    else:
        for i, rule in enumerate(rules):
            W("def p_%s_%d(p):" % (name, i+1))
            W("    '''%s : %s'''" % (name, rule))
            W("    #  %s   %s" % (" " * len(name), numbers(rule)))
            r = "%s : %s" % (name, rule)
            # if r in actions:
            #     W(actions[r])
            # else:
            # W("    raise NotImplementedError")
            W("    print(\"%s\")" % r)
    
grammar_lines = grammar_text.splitlines()

for definition in definition_list:
    if definition.name in ("single_input", "eval_input"):
        continue

    rules = []
    need_list = []
    for terms in flatten(definition.name, definition.expr, need_list):
        rules.append( " ".join(terms) )

    W("\n# " + 
      "\n# ".join(grammar_lines[definition.first_line-1:definition.last_line]))
    format_function(definition.name, rules)

    while need_list:
        name, expr = need_list.pop(0)
        rules = []
        for terms in flatten(name, expr, need_list):
            rules.append( " ".join(terms) )
        rules = rules + [name + " " + rule for rule in rules]
        W("")
        format_function(name, rules)

W('''\ndef p_error(p):
    raise SyntaxError(p)

def parse(source, fileName="<unknown>"):
    lexer = lex.lex()
    parser = yacc.yacc()
    return parser.parse(source, lexer=lexer)
''')

    # lexer = p.lexer
    # if isinstance(lexer, PythonLexer):
    #     lexer = lexer.lexer
    # pos = lexer.kwds(lexer.lexpos)
    # line = re.split("\\r?\\n", lexer.source)[max(pos["lineno"] - 3, 0):pos["lineno"]]
    # indicator = "-" * pos["col_offset"] + "^"
    # raise SyntaxError("invalid syntax\\n  File " + lexer.fileName + ", line " + str(pos["lineno"]) + " col " + str(pos["col_offset"]) + "\\n    " + "\\n    ".join(line) + "\\n----" + indicator)

# (debug=False, write_tables=True, tabmodule="%s_table", errorlog=yacc.NullLogger())
#  % inputGrammar.replace(".g", "")

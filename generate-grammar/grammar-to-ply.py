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

Use it like this:

    generate-grammar/grammar-to-ply.py generate-grammar/femtocode.g generate-grammar/actions.py femtocode/parser.py
"""

import datetime
import itertools
import re
import sys
import time

from femtocode.thirdparty.ply import lex, yacc

inputGrammar, grammarActions, outputPLY, = sys.argv[1:]

execfile(grammarActions)

duplicates = ["atom : LSQB atom_star RSQB"]

literal_to_name = {
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "in": "IN",
    "is": "IS",
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "def": "DEF",

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
    r"//.*"
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
import sys
import tokenize
from ast import literal_eval

from femtocode.thirdparty.ply import lex
from femtocode.thirdparty.ply import yacc

from femtocode.asts.parsingtree import *
''' % (datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H:%M:%S'), " ".join(sys.argv[1:])))

W('''class ProgrammingError(Exception): pass   # my mistake, not the user; user should NEVER see this  :)
class FemtocodeError(Exception): pass     # error in the user Femtocode

def complain(message, source, pos, lineno, col_offset, sourceName, length):
    start = source.rfind("\\n", 0, pos)
    if start == -1: start = 0
    start = source.rfind("\\n", 0, start)
    if start == -1: start = 0
    end = source.find("\\n", pos)
    if end == -1:
        snippet = source[start:]
    else:
        snippet = source[start:end]
    snippet = "    " + snippet.replace("\\n", "\\n    ")
    indicator = "-" * col_offset + "^" * length
    if sourceName == "<string>":
        where = ""
    else:
        where = "in \\"" + sourceName + "\\""
    if "\n" in message:
        at = "At"
    else:
        at = "    at"
    raise FemtocodeError("%s\n%s line:col %d:%d (pos %d)%s:\n\n%s\n----%s\n" % (message, at, lineno, col_offset, pos, where, snippet, indicator))
''')

W("reserved = {\n%s  }\n" % "".join("  '%s': '%s',\n" % (literal, name) for literal, name in literal_to_name.items() if literal.isalpha()))

W("tokens = [%s]\n" % ", ".join("'%s'" % name for literal, name in literal_to_name.items() if literal.isalpha()))

W('''def t_MULTILINESTRING(t):
    r'(\\'\\'\\'[^\\\\]*(\\\\.[^\\\\]*)*\\'\\'\\'|"""[^\\\\]*(\\\\.[^\\\\]*)*""")'
    t.value = literal_eval(t.value), kwds(t.lexer, len(t.value))
    return t
tokens.append("MULTILINESTRING")
''')

W('''def t_STRING(t):
    r'(\\'[^\\n\\'\\\\]*(\\\\.[^\\n\\'\\\\]*)*\\'|"[^\\n"\\\\]*(\\\\.[^\\n"\\\\]*)*")'
    t.value = literal_eval(t.value), kwds(t.lexer, len(t.value))
    return t
tokens.append("STRING")

def t_IMAG_NUMBER(t):
    r"(\\d+[jJ]|((\\d+\\.\\d*|\\.\\d+)([eE][-+]?\\d+)?|\\d+[eE][-+]?\\d+)[jJ])"
    t.value = float(t.value[:-1]) * 1j, kwds(t.lexer, len(t.value))
    return t
tokens.append("IMAG_NUMBER")

def t_FLOAT_NUMBER(t):
    r"((\\d+\\.\\d*|\\.\\d+)([eE][-+]?\\d+)?|\\d+[eE][-+]?\\d+)"
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
''')

W("tokens.extend([%s])\n" % ", ".join("'%s'" % name for literal, name in literal_to_name.items() if not literal.isalpha()))

W("literals = [%s]\n" % ", ".join("'%s'" % literal for literal, name in literal_to_name.items() if not literal.isalpha() and len(literal) == 1 and literal != "\n"))

for literal, name in literal_to_name.items():
    if not literal.isalpha() and len(literal) == 2:
        W('''def t_%s(t):
    r"%s"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t
''' % (name, re.escape(literal)))

for literal, name in literal_to_name.items():
    if not literal.isalpha() and len(literal) == 1:
        W('''def t_%s(t):
    r"%s"
    t.value = t.value, kwds(t.lexer, len(t.value))
    return t
''' % (name, re.escape(literal)))

W('''def t_error(t):
    complain("Unrecognizable token \\"" + t.value + "\\".", t.lexer.source, t.lexer.lexpos, t.lexer.lineno, t.lexer.lexpos - t.lexer.last_col0 + 1, t.lexer.sourceName, t.value[1]["length"])
''')
W('''def t_comment(t):
    r"[ ]*\\043[^\\n]*"  # \\043 is # ; otherwise PLY thinks it is a regex comment
    pass
''')
W('''t_ignore = " \\t\\f"

def t_newline(t):
    r"\\n"
    t.value = t.value, kwds(t.lexer, len(t.value))
    t.lexer.lineno += 1
    t.lexer.last_col0 = t.lexer.lexpos + 1
''')

W('''def inherit_lineno(p0, px, alt=True):
    if isinstance(px, dict):
        p0.source = px["source"]
        p0.pos = px["pos"]
        p0.lineno = px["lineno"]
        p0.col_offset = px["col_offset"]
        p0.sourceName = px["sourceName"]
        p0.length = px["length"]
    else:
        p0.source = px.source
        p0.pos = px.pos
        p0.lineno = px.lineno
        p0.col_offset = px.col_offset
        p0.sourceName = px.sourceName
        p0.length = px.length
        if alt and hasattr(px, "alt"):
            p0.lineno = px.alt["lineno"]
            p0.col_offset = px.alt["col_offset"]

def unwrap_left_associative(args, alt=False):
    out = BinOp(args[0], args[1], args[2])
    inherit_lineno(out, args[0])
    args = args[3:]
    while len(args) > 0:
        out = BinOp(out, args[0], args[1])
        inherit_lineno(out, out.left)
        if alt:
            out.alt = {"lineno": out.lineno, "col_offset": out.col_offset}
            inherit_lineno(out, out.op)
        args = args[2:]
    return out

def unpack_trailer(atom, power_star):
    out = atom
    for trailer in power_star:
        if isinstance(trailer, FcnCall):
            trailer.function = out
            inherit_lineno(trailer, out)
            out = trailer
        elif isinstance(trailer, Attribute):
            trailer.value = out
            inherit_lineno(trailer, out, alt=False)
            if hasattr(out, "alt"):
                trailer.alt = out.alt
            out = trailer
        elif isinstance(trailer, Subscript):
            trailer.value = out
            inherit_lineno(trailer, out)
            out = trailer
        else:
            assert False
    return out
''')
# coverage = {}

def numbers(s):
    return " ".join(("%" + str(len(x)) + "d") % (i+1) for i, x in enumerate(s.split()))

def format_function(name, rules):
    if len(rules) == 1:
        if "%s : %s" % (name, rules[0]) not in duplicates:
            # W("coverage[\"%s : %s\"] = False" % (name, rules[0]))
            W("def p_%s(p):" % name)
            W("    '''%s : %s'''" % (name, rules[0]))
            W("    #  %s   %s" % (" " * len(name), numbers(rules[0])))
            r = "%s : %s" % (name, rules[0])
            # W("    print(\"%s : %s\")" % (name, rules[0]))
            if r in actions:
                # W("    if \"%s : %s\" in coverage: del coverage[\"%s : %s\"]" % (name, rules[0], name, rules[0]))
                W(actions[r])
                del actions[r]
            else:
                W("    raise NotImplementedError")

    else:
        for i, rule in enumerate(rules):
            if "%s : %s" % (name, rule) not in duplicates:
                # W("coverage[\"%s : %s\"] = False" % (name, rule))
                W("def p_%s_%d(p):" % (name, i+1))
                W("    '''%s : %s'''" % (name, rule))
                W("    #  %s   %s" % (" " * len(name), numbers(rule)))
                r = "%s : %s" % (name, rule)
                # W("    print(\"%s : %s\")" % (name, rule))
                if r in actions:
                    # W("    if \"%s : %s\" in coverage: del coverage[\"%s : %s\"]" % (name, rule, name, rule))
                    W(actions[r])
                    del actions[r]
                else:
                    W("    raise NotImplementedError")
    
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
''')

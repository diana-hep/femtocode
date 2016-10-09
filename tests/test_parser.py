#!/usr/bin/env python

# Copyright 2016 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import re
import sys
import unittest

from femtocode.parser import parse
from femtocode.asts.parsingtree import *

import sys

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestParser(unittest.TestCase):
    def runTest(self):
        pass

    def check(self, source, theirs=None):
        if theirs is None:
            theirs = ast.parse(source).body[0].value
            mine = parse(source).expression
        else:
            mine = parse(source)

        # verify that even the line numbers are the same
        global same, treeOne, treeTwo
        same = True
        treeOne = ""
        treeTwo = ""
        def deepcompare(one, two, indent):
            global same, treeOne, treeTwo
            if isinstance(one, ast.AST):
                if not (isinstance(two, ast.AST) and one._fields == two._fields and one.__class__ == two.__class__):
                    same = False
                if not (getattr(one, "lineno", "?") == getattr(two, "lineno", "?") and getattr(one, "col_offset", "?") == getattr(two, "col_offset", "?")):
                    if hasattr(one, "lineno") and hasattr(one, "col_offset"):
                        # Python's lineno/col_offset for strings with line breaks is wrong.
                        # Don't count it against my implementation for getting it right.
                        if not isinstance(one, ast.Str) and not (isinstance(one, ast.Expr) and isinstance(one.value, ast.Str)):
                            same = False
                if not (hasattr(two, "lineno") and hasattr(two, "col_offset")):
                    raise Exception
                treeOne += one.__class__.__name__ + " " + str(getattr(one, "lineno", "?")) + ":" + str(getattr(one, "col_offset", "?")) + "\n"
                treeTwo += two.__class__.__name__ + " " + str(getattr(two, "lineno", "?")) + ":" + str(getattr(two, "col_offset", "?")) + "\n"
                for attrib  in one._fields:
                    treeOne += indent + "  " + attrib + ": "
                    treeTwo += indent + "  " + attrib + ": "
                    valueOne = getattr(one, attrib)
                    valueTwo = getattr(two, attrib)
                    if isinstance(valueOne, list):
                        if not (isinstance(valueTwo, list) and len(valueOne) == len(valueTwo)):
                            same = False
                        if len(valueOne) == 0:
                            treeOne += "[]\n"
                        else:
                            treeOne += "\n"
                        if len(valueTwo) == 0:
                            treeTwo += "[]\n"
                        else:
                            treeTwo += "\n"
                        for x, y in zip(valueOne, valueTwo):
                            treeOne += indent + "    - "
                            treeTwo += indent + "    - "
                            deepcompare(x, y, indent + "        ")
                    elif isinstance(valueOne, (ast.Load, ast.Store, ast.Param, ast.Del)):
                        if not (isinstance(valueTwo, (ast.Load, ast.Store, ast.Param, ast.Del))):
                            same = False
                        treeOne += valueOne.__class__.__name__ + "\n"
                        treeTwo += valueTwo.__class__.__name__ + "\n"
                    elif isinstance(valueOne, ast.AST):
                        if not (isinstance(valueTwo, ast.AST)):
                            same = False
                        deepcompare(valueOne, valueTwo, indent + "    ")
                    elif valueOne is None or isinstance(valueOne, (int, long, float, complex, basestring)):
                        if not (valueOne == valueTwo):
                            same = False
                        treeOne += repr(valueOne) + "\n"
                        treeTwo += repr(valueTwo) + "\n"
                    else:
                        raise Exception
            else:
                if not (one == two):
                    same = False

        deepcompare(theirs, mine, "")
        if not same:
            sys.stderr.write("Error in parsing: " + source + "\n\n")
            treeOne = treeOne.split("\n")
            treeTwo = treeTwo.split("\n")
            width = max(len(x) for x in treeOne) + 3
            x = "Expected"
            y = "Parser output"
            diff = x != re.sub("\s*\(.*\)", "", y)
            while len(x) < width:
                x += " "
            sys.stderr.write(x + "| " + y + "\n")
            x = "-" * len(x)
            sys.stderr.write(x + "+-" + x + "\n")

            while len(treeOne) < len(treeTwo):
                treeOne.append("")
            while len(treeTwo) < len(treeOne):
                treeTwo.append("")
            for x, y in zip(treeOne, treeTwo):
                diff = x != re.sub("\s*\(.*\)", "", y)
                while len(x) < width:
                    x += " "
                if diff:
                    sys.stderr.write(x + "| " + y + "\n")
                else:
                    sys.stderr.write(x + "  " + y + "\n")
            sys.exit(-1)   # too much output to see all at once

    def test_PythonCompatibility(self):
        self.check('"hello"')
        self.check('"he\\nllo"')
        self.check('"he\\\\nllo"')
        self.check('"he\\"\\\\nllo"')
        self.check('"he\'\\"\\\\nllo"')
        self.check('"he\'\\"\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3llo"')
        self.check('"he\'\\"\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\\N{LATIN SMALL LETTER ETH}llo"')

        self.check('"""hello"""')
        self.check('"""he\\nllo"""')
        self.check('"""he\\\\nllo"""')
        self.check('"""he\\"\\\\nllo"""')
        self.check('"""he\'\\"\\\\nllo"""')
        self.check('"""he\'\\"\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3llo"""')
        self.check('"""he\'\\"\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\\N{LATIN SMALL LETTER ETH}llo"""')
        self.check('"""he\'\\"\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\nllo"""')
        self.check('"""he\'\\"\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\n"llo"""')

        self.check("'hello'")
        self.check("'he\\nllo'")
        self.check("'he\\\\nllo'")
        self.check("'he\\'\\\\nllo'")
        self.check("'he\"\\'\\\\nllo'")
        self.check("'he\"\\'\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3llo'")
        self.check("'he\"\\'\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\\N{LATIN SMALL LETTER ETH}llo'")

        self.check("'''hello'''")
        self.check("'''he\\nllo'''")
        self.check("'''he\\\\nllo'''")
        self.check("'''he\\'\\\\nllo'''")
        self.check("'''he\"\\'\\\\nllo'''")
        self.check("'''he\"\\'\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3llo'''")
        self.check("'''he\"\\'\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\\N{LATIN SMALL LETTER ETH}llo'''")
        self.check("'''he\"\\'\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\nllo'''")
        self.check("'''he\"\\'\\\\n\\a\\b\\f\\r\\t\\v\\123\\o123\\xf3\n'llo'''")

        self.check('''.3''')
        self.check('''-3''')
        self.check('''- 3''')
        self.check('''-  3''')
        self.check('''--3''')
        self.check('''-- 3''')
        self.check('''- -3''')
        self.check('''- - 3''')
        self.check('''- -  3''')
        self.check('''+3''')
        self.check('''+ 3''')
        self.check('''+  3''')
        self.check('''++3''')
        self.check('''++ 3''')
        self.check('''+ +3''')
        self.check('''+ + 3''')
        self.check('''+ +  3''')
        self.check('''+-3''')
        self.check('''+- 3''')
        self.check('''+ -3''')
        self.check('''+ - 3''')
        self.check('''+ -  3''')
        self.check('''-+3''')
        self.check('''-+ 3''')
        self.check('''- +3''')
        self.check('''- + 3''')
        self.check('''- +  3''')
        self.check('''-3.14''')
        self.check('''- 3.14''')
        self.check('''-  3.14''')
        self.check('''--3.14''')
        self.check('''-- 3.14''')
        self.check('''- -3.14''')
        self.check('''- - 3.14''')
        self.check('''- -  3.14''')
        self.check('''+3.14''')
        self.check('''+ 3.14''')
        self.check('''+  3.14''')
        self.check('''++3.14''')
        self.check('''++ 3.14''')
        self.check('''+ +3.14''')
        self.check('''+ + 3.14''')
        self.check('''+ +  3.14''')
        self.check('''+-3.14''')
        self.check('''+- 3.14''')
        self.check('''+ -3.14''')
        self.check('''+ - 3.14''')
        self.check('''+ -  3.14''')
        self.check('''-+3.14''')
        self.check('''-+ 3.14''')
        self.check('''- +3.14''')
        self.check('''- + 3.14''')
        self.check('''- +  3.14''')
        self.check('''-3e1''')
        self.check('''- 3e1''')
        self.check('''-  3e1''')
        self.check('''--3e1''')
        self.check('''-- 3e1''')
        self.check('''- -3e1''')
        self.check('''- - 3e1''')
        self.check('''- -  3e1''')
        self.check('''+3e1''')
        self.check('''+ 3e1''')
        self.check('''+  3e1''')
        self.check('''++3e1''')
        self.check('''++ 3e1''')
        self.check('''+ +3e1''')
        self.check('''+ + 3e1''')
        self.check('''+ +  3e1''')
        self.check('''+-3e1''')
        self.check('''+- 3e1''')
        self.check('''+ -3e1''')
        self.check('''+ - 3e1''')
        self.check('''+ -  3e1''')
        self.check('''-+3e1''')
        self.check('''-+ 3e1''')
        self.check('''- +3e1''')
        self.check('''- + 3e1''')
        self.check('''- +  3e1''')

        self.check('''[]''')
        self.check('''[3]''')
        self.check('''[3,]''')
        self.check('''[3, 4]''')
        self.check('''[3, 4,]''')
        self.check('''[3, 4, 5]''')
        self.check('''[3, 4, 5,]''')
        self.check('''[3, 4, 5, 6]''')
        self.check('''[3, 4, 5, 6,]''')

        self.check('''[[1], 2, 3, 4, 5]''')
        self.check('''[[1, 2], 3, 4, 5]''')
        self.check('''[[1, 2, 3], 4, 5]''')
        self.check('''[[1, 2, 3, 4], 5]''')
        self.check('''[[1, 2, 3, 4, 5]]''')
        self.check('''[[[1], 2, 3, 4, 5]]''')
        self.check('''[[[1, 2], 3, 4, 5]]''')
        self.check('''[[[1, 2, 3], 4, 5]]''')
        self.check('''[[[1, 2, 3, 4], 5]]''')
        self.check('''[[[1, 2, 3, 4, 5]]]''')

        self.check('''[1, 2, 3, 4, [5]]''')
        self.check('''[1, 2, 3, [4, 5]]''')
        self.check('''[1, 2, [3, 4, 5]]''')
        self.check('''[1, [2, 3, 4, 5]]''')
        self.check('''[[1, 2, 3, 4, [5]]]''')
        self.check('''[[1, 2, 3, [4, 5]]]''')
        self.check('''[[1, 2, [3, 4, 5]]]''')
        self.check('''[[1, [2, 3, 4, 5]]]''')

        self.check('''3
    ''')
        self.check('''3

    ''')
        self.check('''3


    ''')
        self.check('''3



    ''')
        self.check('''
3''')
        self.check('''

3''')
        self.check('''


3''')
        self.check('''



3''')

        self.check('''a''')
        self.check('''a.b''')
        self.check('''a.b.c''')
        self.check('''a.b.c.d''')
        self.check('''a.b.c.d.e''')
        self.check('''a[1]''')
        self.check('''a[1][2]''')
        self.check('''a[1][2][3]''')
        self.check('''a[1][2][3][4]''')
        self.check('''(9).stuff''')
        self.check('''((9)).stuff''')
        self.check('''(((9))).stuff''')

        self.check('''a[1]''')
        self.check('''a["hey"]''')
        self.check('''a[1:2]''')
        self.check('''a[:]''')
        self.check('''a[1:]''')
        self.check('''a[:1]''')
        self.check('''a[::]''')
        self.check('''a[1::]''')
        self.check('''a[:1:]''')
        self.check('''a[::1]''')
        self.check('''a[1:2:]''')
        self.check('''a[:1:2]''')
        self.check('''a[1::2]''')
        self.check('''a[1:2:3]''')
        self.check('''a[1,]''')
        self.check('''a["hey",]''')
        self.check('''a[1:2,]''')
        self.check('''a[:,]''')
        self.check('''a[1:,]''')
        self.check('''a[:1,]''')
        self.check('''a[::,]''')
        self.check('''a[1::,]''')
        self.check('''a[:1:,]''')
        self.check('''a[::1,]''')
        self.check('''a[1:2:,]''')
        self.check('''a[:1:2,]''')
        self.check('''a[1::2,]''')
        self.check('''a[1:2:3,]''')
        self.check('''a[1,5]''')
        self.check('''a["hey",5]''')
        self.check('''a[1:2,5]''')
        self.check('''a[:,5]''')
        self.check('''a[1:,5]''')
        self.check('''a[:1,5]''')
        self.check('''a[::,5]''')
        self.check('''a[1::,5]''')
        self.check('''a[:1:,5]''')
        self.check('''a[::1,5]''')
        self.check('''a[1:2:,5]''')
        self.check('''a[:1:2,5]''')
        self.check('''a[1::2,5]''')
        self.check('''a[1:2:3,5]''')
        self.check('''a[1,5,]''')
        self.check('''a["hey",5,]''')
        self.check('''a[1:2,5,]''')
        self.check('''a[:,5,]''')
        self.check('''a[1:,5,]''')
        self.check('''a[:1,5,]''')
        self.check('''a[::,5,]''')
        self.check('''a[1::,5,]''')
        self.check('''a[:1:,5,]''')
        self.check('''a[::1,5,]''')
        self.check('''a[1:2:,5,]''')
        self.check('''a[:1:2,5,]''')
        self.check('''a[1::2,5,]''')
        self.check('''a[1:2:3,5,]''')
        self.check('''a[1,"a":"b"]''')
        self.check('''a["hey","a":"b"]''')
        self.check('''a[1:2,"a":"b"]''')
        self.check('''a[:,"a":"b"]''')
        self.check('''a[1:,"a":"b"]''')
        self.check('''a[:1,"a":"b"]''')
        self.check('''a[::,"a":"b"]''')
        self.check('''a[1::,"a":"b"]''')
        self.check('''a[:1:,"a":"b"]''')
        self.check('''a[::1,"a":"b"]''')
        self.check('''a[1:2:,"a":"b"]''')
        self.check('''a[:1:2,"a":"b"]''')
        self.check('''a[1::2,"a":"b"]''')
        self.check('''a[1:2:3,"a":"b"]''')
        self.check('''a[1,"a":"b",]''')
        self.check('''a["hey","a":"b",]''')
        self.check('''a[1:2,"a":"b",]''')
        self.check('''a[:,"a":"b",]''')
        self.check('''a[1:,"a":"b",]''')
        self.check('''a[:1,"a":"b",]''')
        self.check('''a[::,"a":"b",]''')
        self.check('''a[1::,"a":"b",]''')
        self.check('''a[:1:,"a":"b",]''')
        self.check('''a[::1,"a":"b",]''')
        self.check('''a[1:2:,"a":"b",]''')
        self.check('''a[:1:2,"a":"b",]''')
        self.check('''a[1::2,"a":"b",]''')
        self.check('''a[1:2:3,"a":"b",]''')
        self.check('''a[1,5,6]''')
        self.check('''a["hey",5,6]''')
        self.check('''a[1:2,5,6]''')
        self.check('''a[:,5,6]''')
        self.check('''a[1:,5,6]''')
        self.check('''a[:1,5,6]''')
        self.check('''a[::,5,6]''')
        self.check('''a[1::,5,6]''')
        self.check('''a[:1:,5,6]''')
        self.check('''a[::1,5,6]''')
        self.check('''a[1:2:,5,6]''')
        self.check('''a[:1:2,5,6]''')
        self.check('''a[1::2,5,6]''')
        self.check('''a[1:2:3,5,6]''')
        self.check('''a[1,5,6,]''')
        self.check('''a["hey",5,6,]''')
        self.check('''a[1:2,5,6,]''')
        self.check('''a[:,5,6,]''')
        self.check('''a[1:,5,6,]''')
        self.check('''a[:1,5,6,]''')
        self.check('''a[::,5,6,]''')
        self.check('''a[1::,5,6,]''')
        self.check('''a[:1:,5,6,]''')
        self.check('''a[::1,5,6,]''')
        self.check('''a[1:2:,5,6,]''')
        self.check('''a[:1:2,5,6,]''')
        self.check('''a[1::2,5,6,]''')
        self.check('''a[1:2:3,5,6,]''')

        self.check('''a[2].three''')
        self.check('''a.three''')
        self.check('''a[2]''')
        self.check('''a.three[2]''')

        self.check('''x and y''')
        self.check('''x and y and z''')
        self.check('''x and y and z and w''')
        self.check('''not x''')
        self.check('''not x and y''')
        self.check('''x or y''')
        self.check('''x or y and z''')
        self.check('''x or y or z''')
        self.check('''not x or y and z''')
        self.check('''x or not y and z''')
        self.check('''x or y and not z''')
        self.check('''not x or not y and z''')
        self.check('''not x or y and not z''')
        self.check('''x or not y and not z''')
        self.check('''not x or not y and not z''')
        self.check('''x and y or z''')
        self.check('''not x and y or z''')
        self.check('''x and not y or z''')
        self.check('''x and y or not z''')
        self.check('''not x and not y or z''')
        self.check('''not x and y or not z''')
        self.check('''x and not y or not z''')

        self.check('''x < y''')
        self.check('''x > y''')
        self.check('''x == y''')
        self.check('''x >= y''')
        self.check('''x <= y''')
        self.check('''x != y''')
        self.check('''x in y''')
        self.check('''x not in y''')
        self.check('''1 < y < 2''')
        self.check('''1 < y == 2''')

        self.check('''(x) < y''')
        self.check('''(x) > y''')
        self.check('''(x) == y''')
        self.check('''(x) >= y''')
        self.check('''(x) <= y''')
        self.check('''(x) != y''')
        self.check('''(x) in y''')
        self.check('''(x) not in y''')
        self.check('''(1) < y < 2''')
        self.check('''(1) < y == 2''')

        self.check('''x < (y)''')
        self.check('''x > (y)''')
        self.check('''x == (y)''')
        self.check('''x >= (y)''')
        self.check('''x <= (y)''')
        self.check('''x != (y)''')
        self.check('''x in (y)''')
        self.check('''x not in (y)''')
        self.check('''1 < (y) < 2''')
        self.check('''1 < (y) == 2''')
        self.check('''1 < y < (2)''')
        self.check('''1 < y == (2)''')

        self.check('''(x) < (y)''')
        self.check('''(x) > (y)''')
        self.check('''(x) == (y)''')
        self.check('''(x) >= (y)''')
        self.check('''(x) <= (y)''')
        self.check('''(x) != (y)''')
        self.check('''(x) in (y)''')
        self.check('''(x) not in (y)''')
        self.check('''(1) < (y) < 2''')
        self.check('''(1) < (y) == 2''')
        self.check('''(1) < y < (2)''')
        self.check('''(1) < y == (2)''')

        self.check('''x + y''')
        self.check('''x + y + z''')
        self.check('''x + y + z + w''')
        self.check('''x - y''')
        self.check('''x - y - z''')
        self.check('''x - y - z - w''')
        self.check('''x - y + z - w''')
        self.check('''x * y''')
        self.check('''x * y * z''')
        self.check('''x * y * z * w''')
        self.check('''x * y - z * w''')
        self.check('''x / y''')
        self.check('''x / y / z''')
        self.check('''x / y / z / w''')
        self.check('''x / y * z / w''')
        self.check('''x % y''')
        self.check('''x % y % z''')
        self.check('''x % y % z % w''')
        self.check('''x % y / z % w''')
        self.check('''x // y''')
        self.check('''x // y // z''')
        self.check('''x // y // z // w''')
        self.check('''x // y % z // w''')
        self.check('''+x''')
        self.check('''-x''')
        self.check('''++x''')
        self.check('''+-x''')
        self.check('''-+x''')
        self.check('''--x''')
        self.check('''+x + y''')
        self.check('''-x + y''')
        self.check('''++x + y''')
        self.check('''+-x + y''')
        self.check('''-+x + y''')
        self.check('''--x + y''')
        self.check('''x + +x''')
        self.check('''x + -x''')
        self.check('''x + ++x''')
        self.check('''x + +-x''')
        self.check('''x + -+x''')
        self.check('''x + --x''')
        self.check('''x ** y''')
        self.check('''x ** y ** z''')
        self.check('''x ** y ** z ** w''')
        self.check('''x ** y // z ** w''')
        self.check('''x.y**2''')

    def test_zzzNewForms(self):
        self.check('{x => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x, y => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x, y, z => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param()), Name(id='z', ctx=Param())], defaults=[None, None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x, => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x, y, => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x, y, z, => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param()), Name(id='z', ctx=Param())], defaults=[None, None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x=1 => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[Num(n=1)], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x=1, y=1 => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[Num(n=1), Num(n=1)], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x=1, y=1, z=1 => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param()), Name(id='z', ctx=Param())], defaults=[Num(n=1), Num(n=1), Num(n=1)], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x=1, => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[Num(n=1)], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x=1, y=1, => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[Num(n=1), Num(n=1)], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x=1, y=1, z=1, => x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param()), Name(id='z', ctx=Param())], defaults=[Num(n=1), Num(n=1), Num(n=1)], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('f({x => x})', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))], names=[], named=[])))
        self.check('f({x, y => x})', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))], names=[], named=[])))
        self.check('f({x, => x})', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))], names=[], named=[])))
        self.check('f({x, y, => x})', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))], names=[], named=[])))
        self.check('f(x => x)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))], names=[], named=[])))
        self.check('f(x => {x})', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))], names=[], named=[])))
        self.check('{x => x}()', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[], names=[], named=[])))
        self.check('{x, y => x}()', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[], names=[], named=[])))
        self.check('{x, => x}()', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[], names=[], named=[])))
        self.check('{x, y, => x}()', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[], names=[], named=[])))
        self.check('{x => x}(1)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x, y => x}(1)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x, => x}(1)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x, y, => x}(1)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x => x}(1,)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x, y => x}(1,)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x, => x}(1,)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('{x, y, => x}(1,)', Suite(assignments=[], expression=FcnCall(function=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))), positional=[Num(n=1)], names=[], named=[])))
        self.check('z = {x => x}; z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x => x} z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x, y => x}; z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x, y => x} z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x, => x}; z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x, => x} z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x, y, => x}; z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))
        self.check('z = {x, y, => x} z', Suite(assignments=[Assignment(lvalues=[Name(id='z', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='z', ctx=Load())))

        self.check('{x => x;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x => x;;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x => x;;;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x; x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load()))], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x; x;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load()))], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x; x}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load()))], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x; x;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load()))], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x;; x;;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load()))], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x;;; x;;;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load()))], expression=Name(id='x', ctx=Load())))))
        self.check('{x => y = x; z=y; z}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load())), Assignment(lvalues=[Name(id='z', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='z', ctx=Load())))))
        self.check('{x => y = x; z=y; z;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load())), Assignment(lvalues=[Name(id='z', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='z', ctx=Load())))))
        self.check('{x => y = x; z=y; z}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load())), Assignment(lvalues=[Name(id='z', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='z', ctx=Load())))))
        self.check('{x => y = x; z=y; z;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load())), Assignment(lvalues=[Name(id='z', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='z', ctx=Load())))))
        self.check('{x => y = x; z=y; z;;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load())), Assignment(lvalues=[Name(id='z', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='z', ctx=Load())))))
        self.check('{x => y = x;;; z=y;;; z;;;}', Suite(assignments=[], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Name(id='x', ctx=Load())), Assignment(lvalues=[Name(id='z', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='z', ctx=Load())))))

        self.check('f()', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[], names=[], named=[])))
        self.check('f(x)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load())], names=[], named=[])))
        self.check('f(x,)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load())], names=[], named=[])))
        self.check('f(x, y)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load()), Name(id='y', ctx=Load())], names=[], named=[])))
        self.check('f(x, y,)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load()), Name(id='y', ctx=Load())], names=[], named=[])))
        self.check('f(x, y, z)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load()), Name(id='y', ctx=Load()), Name(id='z', ctx=Load())], names=[], named=[])))
        self.check('f(x, y, z,)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load()), Name(id='y', ctx=Load()), Name(id='z', ctx=Load())], names=[], named=[])))
        self.check('f(x=1)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[], names=[Name(id='x', ctx=Param())], named=[Num(n=1)])))
        self.check('f(x=1,)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[], names=[Name(id='x', ctx=Param())], named=[Num(n=1)])))
        self.check('f(x=1, y)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='y', ctx=Load())], names=[Name(id='x', ctx=Param())], named=[Num(n=1)])))
        self.check('f(x, y=1,)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load())], names=[Name(id='y', ctx=Param())], named=[Num(n=1)])))
        self.check('f(x, y, z=1)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load()), Name(id='y', ctx=Load())], names=[Name(id='z', ctx=Param())], named=[Num(n=1)])))
        self.check('f(x, y=1, z,)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[Name(id='x', ctx=Load()), Name(id='z', ctx=Load())], names=[Name(id='y', ctx=Param())], named=[Num(n=1)])))

        self.check('x = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x): x; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x): x; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x) {x} x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x) {x}; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x,): x; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x,) {x} x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x,) {x}; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param())], defaults=[None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x, y): x; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x, y,) {x} x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x, y,) {x}; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x, y,) {x = y; x} x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('def f(x, y,) {x = y; x}; x', Suite(assignments=[Assignment(lvalues=[Name(id='f', ctx=Store())], expression=FcnDef(parameters=[Name(id='x', ctx=Param()), Name(id='y', ctx=Param())], defaults=[None, None], body=Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Name(id='y', ctx=Load()))], expression=Name(id='x', ctx=Load()))))], expression=Name(id='x', ctx=Load())))

        self.check('@', Suite(assignments=[], expression=AtArg(num=None)))
        self.check('f(@)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[AtArg(num=None)], names=[], named=[])))
        self.check('@1', Suite(assignments=[], expression=AtArg(num=1)))
        self.check('f(@1)', Suite(assignments=[], expression=FcnCall(function=Name(id='f', ctx=Load()), positional=[AtArg(num=1)], names=[], named=[])))

        self.check('0x123', Suite(assignments=[], expression=Num(n=291)))
        self.check('0o123', Suite(assignments=[], expression=Num(n=83)))
        self.check('3+4j', Suite(assignments=[], expression=BinOp(left=Num(n=3), op=Add(), right=Num(n=4j))))

        self.check('x = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check(';x = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('x = 1; x;', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check(';x = 1; x;', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check(';;x = 1;; x;;', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check(';;;x = 1;;; x;;;', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('x, = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('x, y = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store()), Name(id='y', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('x, y, = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store()), Name(id='y', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('x, y, z = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store()), Name(id='y', ctx=Store()), Name(id='z', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))
        self.check('x, y, z, = 1; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store()), Name(id='y', ctx=Store()), Name(id='z', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load())))

        self.check('if true: 1 else: 2', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2)))))
        self.check('if true: {1} else: {2}', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2)))))
        self.check('if true {1} else {2}', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2)))))
        self.check('if true {x = 1; x} else {y = 2; y}', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load()))], alternate=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Num(n=2))], expression=Name(id='y', ctx=Load())))))
        self.check('if true: 1 elif false: 2 else: 3', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3)))))
        self.check('if true: {1} elif false: {2} else: {3}', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3)))))
        self.check('if true {1} elif false {2} else {3}', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3)))))
        self.check('if true: 1 elif false: 2 elif true: 3 else: 4', Suite(assignments=[], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load()), Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2)), Suite(assignments=[], expression=Num(n=3))], alternate=Suite(assignments=[], expression=Num(n=4)))))

        self.check('x = if true: 1 else: 2; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true: {1} else: {2}; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true: {1} else: {2} x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true {1} else {2}; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true {1} else {2} x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1))], alternate=Suite(assignments=[], expression=Num(n=2))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true {x = 1; x} else {y = 2; y}; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load()))], alternate=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Num(n=2))], expression=Name(id='y', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true {x = 1; x} else {y = 2; y} x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load())], consequents=[Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=Num(n=1))], expression=Name(id='x', ctx=Load()))], alternate=Suite(assignments=[Assignment(lvalues=[Name(id='y', ctx=Store())], expression=Num(n=2))], expression=Name(id='y', ctx=Load()))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true: 1 elif false: 2 else: 3; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true: {1} elif false: {2} else: {3}; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true: {1} elif false: {2} else: {3} x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true {1} elif false {2} else {3}; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true {1} elif false {2} else {3} x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2))], alternate=Suite(assignments=[], expression=Num(n=3))))], expression=Name(id='x', ctx=Load())))
        self.check('x = if true: 1 elif false: 2 elif true: 3 else: 4; x', Suite(assignments=[Assignment(lvalues=[Name(id='x', ctx=Store())], expression=IfChain(predicates=[Name(id='true', ctx=Load()), Name(id='false', ctx=Load()), Name(id='true', ctx=Load())], consequents=[Suite(assignments=[], expression=Num(n=1)), Suite(assignments=[], expression=Num(n=2)), Suite(assignments=[], expression=Num(n=3))], alternate=Suite(assignments=[], expression=Num(n=4))))], expression=Name(id='x', ctx=Load())))





        import femtocode.parser
        for rule in sorted(femtocode.parser.coverage):
            print(rule)

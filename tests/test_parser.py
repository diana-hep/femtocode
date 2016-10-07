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

        self.check('"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('r"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('u"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905"')
        self.check('ur"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905"')
        self.check('R"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('U"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905"')
        self.check('UR"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905"')
        self.check('Ur"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905"')
        self.check('uR"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905"')
        self.check('b"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('B"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('br"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('Br"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('bR"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('BR"hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo"')
        self.check('\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('r\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('u\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905lo\'')
        self.check('ur\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905lo\'')
        self.check('R\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('U\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905lo\'')
        self.check('UR\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905lo\'')
        self.check('Ur\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905lo\'')
        self.check('uR\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\vlo\\N{LATIN SMALL LETTER ETH}\\u2212\\U00010905lo\'')
        self.check('b\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('B\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('br\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('Br\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('bR\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')
        self.check('BR\'hel\\\n\\\\\\\'\\"\\a\\b\\f\\n\\r\\t\\v\\123\\o123\\xf3lo\'')

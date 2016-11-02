"""
Boolean Algebra.

This module defines a Boolean Algebra over the set {TRUE, FALSE} with boolean
variables and the boolean functions AND, OR, NOT. For extensive documentation
look either into the docs directory or view it online, at
https://booleanpy.readthedocs.org/en/latest/.

Copyright (c) 2009-2010 Sebastian Kraemer, basti.kr@gmail.com
Released under revised BSD license.
"""

from __future__ import absolute_import

from femtocode.thirdparty.boolean.boolean import BooleanAlgebra

from femtocode.thirdparty.boolean.boolean import Expression
from femtocode.thirdparty.boolean.boolean import Symbol
from femtocode.thirdparty.boolean.boolean import ParseError
from femtocode.thirdparty.boolean.boolean import PARSE_ERRORS

from femtocode.thirdparty.boolean.boolean import AND
from femtocode.thirdparty.boolean.boolean import NOT
from femtocode.thirdparty.boolean.boolean import OR

from femtocode.thirdparty.boolean.boolean import TOKEN_TRUE
from femtocode.thirdparty.boolean.boolean import TOKEN_FALSE
from femtocode.thirdparty.boolean.boolean import TOKEN_SYMBOL

from femtocode.thirdparty.boolean.boolean import TOKEN_AND
from femtocode.thirdparty.boolean.boolean import TOKEN_OR
from femtocode.thirdparty.boolean.boolean import TOKEN_NOT

from femtocode.thirdparty.boolean.boolean import TOKEN_LPAR
from femtocode.thirdparty.boolean.boolean import TOKEN_RPAR

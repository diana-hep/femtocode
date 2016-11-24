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

from femtocode.typesystem import *

def literal(schema, operator, value):
    if isinstance(schema, Union):
        possibilities = []
        for p in schema.possibilities:
            result = literal(p, operator, value)
            if not isinstance(result, Impossible):
                possibilities.append(result)

        if len(possibilities) == 0:
            return impossible
        elif len(possibilities) == 1:
            return possibilities[0]
        else:
            return union(*possibilities)

    elif isinstance(schema, Impossible):
        if operator == "==":
            return impossible

        elif operator == "!=":
            return impossible

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Null):
        if value is None:
            if operator == "==":
                return null
            elif operator == "!=":
                return impossible
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

        else:
            if operator == "==":
                return impossible
            elif operator == "!=":
                return null
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Boolean):
        if isinstance(value, bool):
            if operator == "==":
                return boolean
            elif operator == "!=":
                return boolean       # it could be the other one
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

        else:
            if operator == "==":
                return impossible
            elif operator == "!=":
                return boolean
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Number):
        if isinstance(value, (int, long, float)):
            if operator == "==":
                return intersection(schema, Number(value, value, round(value) == value))

            elif operator == "!=":
                return difference(schema, Number(value, value, False))

            elif operator == ">":
                return intersection(schema, Number(almost(value), inf, False))

            elif operator == ">=":
                return intersection(schema, Number(value, inf, False))

            elif operator == "<":
                return intersection(schema, Number(-inf, almost(value), False))

            elif operator == "<=":
                return intersection(schema, Number(-inf, value, False))

            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

        else:
            return impossible

    elif isinstance(schema, String):
        if operator == "==":
            if isinstance(value, string_types):
                return intersection(schema, String("bytes" if isinstance(value, bytes) else "unicode", len(value), len(value)))
            else:
                return impossible

        elif operator == "!=":
            return schema

        elif operator in ("size==", "size!=", "size>", "size>=", "size<", "size<="):
            if isinstance(value, (int, long)):
                operator = {"size==": "==", "size!=": "!=", "size>": ">", "size>=": ">=", "size<": "<", "size<=": "<="}[operator]
                number = literal(Number(schema.fewest, schema.most, True), operator, value)
                if isinstance(number, Number):
                    return String(schema.charset, number.min, number.max)
                elif isinstance(number, Union):
                    return Union([String(schema.charset, p.min, p.max) for p in number.possibilities])
                elif isinstance(number, Impossible):
                    return impossible
                else:
                    raise ProgrammingError("literal(Number, \"{0}\", value) is {1}".format(operator, number))

            else:
                raise ProgrammingError("operator {0} unexpected for value {1}".format(operator, value))

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Collection):
        if operator == "==":
            if isinstance(value, (list, tuple, set)):
                if len(value) == 0:
                    return intersection(schema, empty)
                else:
                    return intersection(schema, Collection(union(*(literal(schema.items, operator, x) for x in value)), len(value), len(value), True))
            else:
                return impossible

        elif operator == "!=":
            if isinstance(value, (list, tuple, set)) and len(value) == 0:
                return difference(schema, empty)
            else:
                return schema

        elif operator in ("size==", "size!=", "size>", "size>=", "size<", "size<="):
            if isinstance(value, (int, long)):
                operator = {"size==": "==", "size!=": "!=", "size>": ">", "size>=": ">=", "size<": "<", "size<=": "<="}[operator]
                number = literal(Number(schema.fewest, schema.most, True), operator, value)
                if isinstance(number, Number):
                    return Collection(schema.items, number.min, number.max, schema.ordered)
                elif isinstance(number, Union):
                    return Union([Collection(schema.items, p.min, p.max, schema.ordered) for p in number.possibilities])
                elif isinstance(number, Impossible):
                    return impossible
                else:
                    raise ProgrammingError("literal(Number, \"{0}\", value) is {1}".format(operator, number))

            else:
                raise ProgrammingError("operator {0} unexpected for value {1}".format(operator, value))

        elif operator == "ordered":
            if schema.ordered:
                return schema
            else:
                return impossible

        elif operator == "notordered":
            if schema.ordered:
                return impossible
            else:
                return schema

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Record):
        if operator == "==":
            if all(hasattr(value, n) for n in schema.fields):
                return intersection(schema, Record(dict((n, literal(t, operator, getattr(value, n))) for n, t in schema.fields.items())))
            else:
                return impossible

        elif operator == "!=":
            return schema

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    else:
        raise ProgrammingError("unhandled schema: {0}".format(schema))



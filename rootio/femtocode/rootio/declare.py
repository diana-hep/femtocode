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
import json
import math
import re
from femtocode.py23 import *

import femtocode.typesystem

import numpy
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.comments import CommentedSeq

class DatasetDeclaration(object):
    class Error(Exception):
        def __init__(self, lc, message):
            self.lc = lc
            self.message = message

        def __repr__(self):
            return "DatasetDeclaration.Error({0}, {1})".format(self.lc, json.dumps(self.message))

        def __str__(self):
            return "On line {0}, {1}".format(self.lc[0], self.message)

    @staticmethod
    def _unrecognized(observe, expect, lc, where):
        unrecognized = set(observe).difference(set(expect))
        if len(unrecognized) > 0:
            raise DatasetDeclaration.Error(lc, "unrecognized keys in {0}: {1}".format(where, ", ".join(sorted(unrecognized))))

    @staticmethod
    def _asbool(value, lc):
        if isinstance(value, bool):
            return value
        elif value == "True" or value == "true":
            return True
        elif value == "False" or value == "false":
            return True
        else:
            raise DatasetDeclaration.Error(lc, "value should be boolean: {0}".format(value))

    @staticmethod
    def _aslimit(value, lc):
        if isinstance(value, string_types):
            module = ast.parse(value)
            if isinstance(module, ast.Module) and len(module.body) == 1 and isinstance(module.body[0], ast.Expr):
                def restrictedeval(expr):
                    if isinstance(expr, ast.Num):
                        return expr.n

                    elif isinstance(expr, ast.Name) and expr.id == "inf":
                        return femtocode.typesystem.inf

                    elif isinstance(expr, ast.Name) and expr.id == "pi":
                        return math.pi

                    elif isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
                        return -restrictedeval(expr.operand)

                    elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
                        return restrictedeval(expr.left) + restrictedeval(expr.right)

                    elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Sub):
                        return restrictedeval(expr.left) - restrictedeval(expr.right)

                    elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Mult):
                        return restrictedeval(expr.left) * restrictedeval(expr.right)

                    elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
                        return restrictedeval(expr.left) / restrictedeval(expr.right)

                    elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Pow):
                        return restrictedeval(expr.left) ** restrictedeval(expr.right)

                    elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "almost" and len(expr.args) == 1 and len(expr.keywords) == 0 and expr.kwargs is None and expr.starargs is None:
                        return femtocode.typesystem.almost(restrictedeval(expr.args[0]))

                    else:
                        raise DatasetDeclaration.Error(lc, "couldn't parse as a min/max/least/most limit: {0}".format(value))

                return restrictedeval(module.body[0].value)

        elif isinstance(value, (int, long, float)):
            return value

        elif isinstance(value, femtocode.typesystem.almost) and isinstance(value.real, (int, long, float)):
            return value

        else:
            raise DatasetDeclaration.Error(lc, "unrecognized type for min/max/least/most limit: {0}".format(value))

    @staticmethod
    def _toschema(quantity):
        if quantity in ("boolean", "number", "real", "integer", "extended", "collection", "vector", "matrix", "tensor", "record"):
            return DatasetDeclaration._toschema({"type": quantity})

        elif isinstance(quantity, CommentedMap):
            def maybe(key):
                try:
                    return quantity.lc.key(key)
                except KeyError:
                    return (quantity.lc.line, quantity.lc.col)

            if quantity.get("type") == "boolean":
                return femtocode.typesystem.boolean

            elif quantity.get("type") == "number" or quantity.get("type") == "real":
                return femtocode.typesystem.Number(
                    min=DatasetDeclaration._aslimit(quantity.get("min", "almost(-inf)"), maybe("min")),
                    max=DatasetDeclaration._aslimit(quantity.get("max", "almost(inf)"), maybe("max")),
                    whole=DatasetDeclaration._asbool(quantity.get("whole", False), maybe("whole")))

            elif quantity.get("type") == "integer":
                return femtocode.typesystem.Number(
                    min=DatasetDeclaration._aslimit(quantity.get("min", "almost(-inf)"), maybe("min")),
                    max=DatasetDeclaration._aslimit(quantity.get("max", "almost(inf)"), maybe("max")),
                    whole=DatasetDeclaration._asbool(quantity.get("whole", True), maybe("whole")))

            elif quantity.get("type") == "extended":
                return femtocode.typesystem.Number(
                    min=DatasetDeclaration._aslimit(quantity.get("min", "-inf"), maybe("min")),
                    max=DatasetDeclaration._aslimit(quantity.get("max", "inf"), maybe("max")),
                    whole=DatasetDeclaration._asbool(quantity.get("whole", False), maybe("whole")))

            elif quantity.get("type") == "collection":
                return femtocode.typesystem.Collection(
                    items=DatasetDeclaration._toschema(quantity.get("items")),
                    fewest=DatasetDeclaration._aslimit(quantity.get("fewest", 0), maybe("fewest")),
                    most=DatasetDeclaration._aslimit(quantity.get("most", "almost(inf)"), maybe("most")))

            elif quantity.get("type") in ("vector", "matrix", "tensor"):
                dimensions = str(quantity.get("dimensions", ""))
                dimensions = re.split(r"\s*,\s*", dimensions.strip())
                for i, x in enumerate(dimensions):
                    try:
                        dimensions[i] = int(dimensions[i])
                    except ValueError:
                        raise DatasetDeclaration.Error(maybe("dimensions"), "dimensions must be comma-separated integers")
                    
                if quantity["type"] == "vector":
                    if len(dimensions) != 1:
                        raise DatasetDeclaration.Error(maybe("dimensions"), "vectors should have exactly one dimension")
                    return femtocode.typesystem.vector(
                        DatasetDeclaration._toschema(quantity.get("items")),
                        *dimensions)

                elif quantity["type"] == "matrix":
                    if len(dimensions) != 2:
                        raise DatasetDeclaration.Error(maybe("dimensions"), "matrices should have exactly two dimensions")
                    return femtocode.typesystem.matrix(
                        DatasetDeclaration._toschema(quantity.get("items")),
                        *dimensions)

                elif quantity["type"] == "tensor":
                    if len(dimensions) <= 2:
                        raise DatasetDeclaration.Error(maybe("dimensions"), "tensors should have more than two dimensions")
                    return femtocode.typesystem.tensor(
                        DatasetDeclaration._toschema(quantity.get("items")),
                        *dimensions)

            elif quantity.get("type") == "record":
                fields = quantity.get("fields")
                if fields is None:
                    raise DatasetDeclaration.Error((quantity.lc.line, quantity.lc.col), "record needs fields")
                elif not isinstance(fields, CommentedMap):
                    raise DatasetDeclaration.Error(maybe("fields"), "record fields must be a mapping")
                return femtocode.typesystem.record(**dict((k, DatasetDeclaration._toschema(v)) for k, v in fields.items()))

            else:
                raise DatasetDeclaration.Error(maybe("type"), "type specification not recognized or not supported for ROOT extraction: type {0}, keys {1}".format(quantity.get("type"), ", ".join(sorted(set(quantity.keys()).difference(set(["type"]))))))

        else:
            raise DatasetDeclaration.Error((quantity.lc.line, quantity.lc.col), "type specification must be a string or dict: {0}".format(quantity))

    class Source(object):
        @staticmethod
        def fromYaml(source):
            DatasetDeclaration._unrecognized(source.keys(), ["format", "paths"], (source.lc.line, source.lc.col), "dataset declaration source")

            format = source.get("format")
            if format is None:
                raise DatasetDeclaration.Error((source.lc.line, source.lc.col), "column-source needs a name")
            elif not isinstance(format, string_types):
                raise DatasetDeclaration.Error(source.lc.get("format"), "name must be a string")

            groupsize = source.get("groupsize", 1)
            if not isinstance(groupsize, (int, long)) or groupsize < 1:
                raise DatasetDeclaration.Error(source.lc.get("groupsize"), "groupsize must be a positive integer")

            paths = source.get("paths")
            if paths is None:
                raise DatasetDeclaration.Error((source.lc.line, source.lc.col), "column-source needs a paths")
            elif not isinstance(paths, CommentedSeq) or not all(isinstance(x, string_types) for x in paths):
                raise DatasetDeclaration.Error(source.lc.get("paths"), "source path must be a list of strings (denoted with '-' in YAML)")

            return DatasetDeclaration.Source(format, groupsize, paths)

        def __init__(self, format, groupsize, paths):
            self.format = format
            self.groupsize = groupsize
            self.paths = paths

        def __repr__(self):
            return "DatasetDeclaration.Source({0}, {1}, [{2}])".format(json.dumps(self.format), self.groupsize, ", ".join(json.dumps(x) for x in self.paths))

    class From(object):
        @staticmethod
        def fromYaml(frm, sources):
            DatasetDeclaration._unrecognized(frm.keys(), ["tree", "branch", "dtype", "sources"], (frm.lc.line, frm.lc.col), "data column from mapping")

            tree = frm.get("tree")
            if tree is None:
                raise DatasetDeclaration.Error((frm.lc.line, frm.lc.col), "column-from needs a tree")
            elif not isinstance(tree, string_types):
                raise DataestDeclaration.Error(frm.lc.get("tree"), "column-from tree must be a string")

            branch = frm.get("branch")
            if branch is None:
                raise DatasetDeclaration.Error((frm.lc.line, frm.lc.col), "column-from needs a branch field")
            elif not isinstance(branch, string_types):
                raise DatasetDeclaration.Error(frm.lc.key("branch"), "branch field must be a string")

            dtype = frm.get("dtype")
            if dtype is None:
                raise DatasetDeclaration.Error((frm.lc.line, frm.lc.col), "column-from needs a dtype field")
            try:
                dtype = str(numpy.dtype(dtype))
            except TypeError:
                raise DatasetDeclaration.Error(frm.lc.key("dtype"), "column-from dtype field must define a Numpy dtype")

            src = frm.get("sources")
            if src is None:
                src = sources
            elif not isinstance(src, CommentedSeq):
                raise DatasetDeclaration.Error(frm.lc.key("sources"), "column-sources must be a list (denoted with '-' in YAML)")
            src = [x if isinstance(x, DatasetDeclaration.Source) else DatasetDeclaration.Source.fromYaml(x) for x in src]

            return DatasetDeclaration.From(tree, branch, dtype, src)

        def __init__(self, tree, branch, dtype, sources):
            self.tree = tree
            self.branch = branch
            self.dtype = dtype
            self.sources = sources

        def __repr__(self):
            return "DatasetDeclaration.From({0}, {1}, {2}, {3})".format(self.tree, self.branch, self.dtype, self.sources)

    class Quantity(object):
        @staticmethod
        def fromYaml(quantity, sources):
            tpe = quantity.get("type")

            if "alias" in quantity:
                raise DatasetDeclaration.Error(quantity.lc.key("alias"), "datasets from ROOT do not support recursive types, so the 'alias' keyword is not allowed")

            if tpe == "boolean":
                DatasetDeclaration._unrecognized(quantity.keys(), ["from", "type"], (quantity.lc.line, quantity.lc.col), "boolean type")
                frm = DatasetDeclaration.From.fromYaml(quantity.get("from"), sources)
                return DatasetDeclaration.Primitive(DatasetDeclaration._toschema(quantity), frm, (quantity.lc.line, quantity.lc.col))

            elif tpe in ("number", "integer", "real", "extended"):
                DatasetDeclaration._unrecognized(quantity.keys(), ["from", "type", "min", "max", "whole"], (quantity.lc.line, quantity.lc.col), "number type")
                frm = DatasetDeclaration.From.fromYaml(quantity.get("from"), sources)
                return DatasetDeclaration.Primitive(DatasetDeclaration._toschema(quantity), frm, (quantity.lc.line, quantity.lc.col))

            elif tpe == "collection":
                DatasetDeclaration._unrecognized(quantity.keys(), ["from", "type", "items", "fewest", "most", "ordered"], (quantity.lc.line, quantity.lc.col), "collection type")
                return DatasetDeclaration.Collection(DatasetDeclaration._toschema(quantity), DatasetDeclaration.Quantity.fromYaml(quantity["items"], sources), (quantity.lc.line, quantity.lc.col))

            elif tpe in ("vector", "matrix", "tensor"):
                DatasetDeclaration._unrecognized(quantity.keys(), ["from", "type", "items", "dimensions"], (quantity.lc.line, quantity.lc.col), "vector/matrix/tensor type")
                return DatasetDeclaration.Collection(DatasetDeclaration._toschema(quantity), DatasetDeclaration.Quantity.fromYaml(quantity["items"], sources), (quantity.lc.line, quantity.lc.col))

            elif tpe == "record":
                DatasetDeclaration._unrecognized(quantity.keys(), ["from", "type", "fields"], (quantity.lc.line, quantity.lc.col), "record type")
                return DatasetDeclaration.Record(DatasetDeclaration._toschema(quantity), dict((k, DatasetDeclaration.Quantity.fromYaml(v, sources)) for k, v in quantity["fields"].items()), (quantity.lc.line, quantity.lc.col))

            else:
                if tpe is None:
                    raise DatasetDeclaration.Error((quantity.lc.line, quantity.lc.col), "quantity needs a type")
                elif not isinstance(tpe, string_types):
                    raise DatasetDeclaration.Error(quantity.lc.key("type"), "quantity must be one of {0}".format(", ".join(["boolean", "number", "integer", "real", "extended", "collection", "vector", "matrix", "tensor", "record"])))

    class Collection(Quantity):
        def __init__(self, schema, items, lc):
            self.schema = schema
            self.items = items
            self.lc = lc

        def __repr__(self):
            return "DatasetDeclaration.Collection({0}, {1}, {2})".format(self.schema, repr(self.items), self.lc)

    class Record(Quantity):
        def __init__(self, schema, fields, lc):
            self.schema = schema
            self.fields = fields
            self.lc = lc

        def __repr__(self):
            return "DatasetDeclaration.Record({0}, {1}, {2})".format(self.schema, ", ".join("{0}={1}".format(k, repr(v)) for k, v in self.fields.items()), self.lc)

    class Primitive(Quantity):
        def __init__(self, schema, frm, lc):
            self.schema = schema
            self.frm = frm
            self.lc = lc

        def __repr__(self):
            return "DatasetDeclaration.Primitive({0}, {1}, {2})".format(self.schema, self.frm, self.lc)

    @staticmethod
    def fromYamlString(declaration):
        return DatasetDeclaration.fromYaml(ruamel.yaml.load(declaration, Loader=ruamel.yaml.RoundTripLoader))

    @staticmethod
    def fromYaml(declaration):
        def resolve(obj, lc, definitions, defining):
            if isinstance(obj, string_types):
                if obj in definitions:
                    if definitions[obj] == defining:
                        raise DatasetDeclaration.Error(lc, "definitions in dataset declaration must not be recursively defined (in \"{0}\")".format(defining))
                    return resolve(definitions[obj], lc, definitions, defining)
                else:
                    return obj

            elif isinstance(obj, (int, long, float)):
                return obj

            elif obj is True or obj is False or obj is None:
                return obj

            elif isinstance(obj, CommentedMap):
                if any(not isinstance(k, string_types) for k in obj.keys()):
                    raise DatasetDeclaration.Error(lc, "mapping keys in dataset declaration must be strings ({0})".format(json.dumps(k)))
                out = CommentedMap((k, resolve(v, obj.lc.key(k), definitions, defining)) for k, v in obj.items())
                out._yaml_line_col = obj.lc
                return out

            elif isinstance(obj, CommentedSeq):
                out = CommentedSeq(resolve(x, obj.lc.key(i), definitions, defining) for i, x in enumerate(obj))
                out._yaml_line_col = obj.lc
                return out

            else:
                raise DatasetDeclaration.Error(lc, "unrecognized object in dataset declaration: {0}".format(obj))

        if not isinstance(declaration, CommentedMap):
            raise DatasetDeclaration.Error((1, 0), "dataset declaration must be a dict (after parsing JSON or YAML)")

        DatasetDeclaration._unrecognized(declaration.keys(), ["define", "name", "sources", "schema"], (declaration.lc.line, declaration.lc.col), "dataset declaration")

        definitions = declaration.get("define", {})
        if not isinstance(definitions, (dict, CommentedMap)):
            raise DatasetDeclaration.Error(declaration.lc.key("define"), "dataset definitions must be a dict: {0}".format(definitions))
        for k in definitions.keys():
            definitions[k] = resolve(definitions[k], declaration.lc.key("define"), definitions, k)

        name = declaration.get("name")
        if name is None:
            raise DatasetDeclaration.Error((declaration.lc.line, declaration.lc.col), "dataset declaration needs a name")
        elif not isinstance(name, string_types):
            raise DatasetDeclaration.Error(declaration.lc.key("name"), "name must be a string")
        name = declaration["name"]   # never resolve it, even if it coincides with a definition--- that would be confusing!

        sources = declaration.get("sources", [])
        if isinstance(sources, list):
            sources_lc = (declaration.lc.line, declaration.lc.col)
        elif isinstance(sources, (list, CommentedSeq)):
            sources_lc = sources.lc
        else:
            raise DatasetDeclaration.Error(declaration.lc.key("sources"), "sources must be a list (denoted with '-' in YAML)")
        sources = CommentedSeq(DatasetDeclaration.Source.fromYaml(resolve(x, declaration.lc.key("sources"), definitions, None)) for x in sources)
        sources._yaml_line_col = sources_lc

        fields = declaration.get("schema")
        if fields is None:
            raise DatasetDeclaration.Error((declaration.lc.line, declaration.lc.col), "dataset declaration needs a schema")
        elif not isinstance(fields, CommentedMap):
            raise DatasetDeclaration.Error(declaration.lc.key("schema"), "schema must be a mapping (no '-' in YAML)")
        elif len(fields) == 0:
            raise DatasetDeclaration.Error(declaration.lc.key("schema"), "schema must not be empty")
        fields = dict((k, DatasetDeclaration.Quantity.fromYaml(resolve(v, declaration.lc.key("schema"), definitions, None), sources)) for k, v in fields.items())

        return DatasetDeclaration(name, fields, (declaration.lc.line, declaration.lc.col))

    def __init__(self, name, fields, lc):
        self.name = name
        self.fields = fields
        self.lc = lc

    def __repr__(self):
        return "DatasetDeclaration({0}, {1})".format(json.dumps(self.name), ", ".join("{0}={1}".format(k, repr(v)) for k, v in self.fields.items()))

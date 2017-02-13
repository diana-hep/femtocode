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
import glob
import re
from femtocode.py23 import *
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import femtocode.typesystem

import strictyaml

def filesFromPath(path):
    url = urlparse(path)
    if url.scheme == "":
        for x in glob.glob(url.path):
            yield x

    elif url.scheme == "root":
        if "**" in url.path:
            raise NotImplementedError("** wildcards not supported in XRootD")

        import XRootD.client
        from XRootD.client.flags import OpenFlags

        fs = XRootD.client.FileSystem("{0}://{1}".format(url.scheme, url.netloc))

        def exists(path):
            return fs.locate(path, OpenFlags.NONE)[0].ok

        def search(path, patterns):
            fullpath = "".join("/" + x for x in path)

            if len(patterns) > 0 and re.search(r"[\*\?\[\]\{\}]", patterns[0]) is None:
                if exists(fullpath + "/" + patterns[0]):
                    for x in search(path + [patterns[0]], patterns[1:]):
                        yield x

            else:
                status, listing = fs.dirlist(fullpath)
                if status.ok:
                    for x in listing.dirlist:
                        if len(patterns) == 0 or glob.fnmatch.fnmatchcase(x.name, patterns[0]):
                            for y in search(path + [x.name], patterns[1:]):
                                yield y

                else:
                    if len(patterns) == 0:
                        yield fullpath

        patterns = re.split(r"/+", url.path.strip("/"))
        for x in search([], patterns):
            yield "{0}://{1}/{2}".format(url.scheme, url.netloc, x)

    else:
        raise IOError("unknown protocol: {0}".format(url.scheme))

class DatasetDeclaration(object):
    class Error(Exception): pass

    @staticmethod
    def _unrecognized(observe, expect, where):
        unrecognized = set(observe).difference(set(expect))
        if len(unrecognized) > 0:
            raise DatasetDeclaration.Error("unrecognized keys in {0}: {1}".format(where, ", ".join(sorted(unrecognized))))

    @staticmethod
    def _asbool(value):
        if isinstance(value, bool):
            return value
        elif value == "True" or value == "true":
            return True
        elif value == "False" or value == "false":
            return True
        else:
            raise DatasetDeclaration.Error("value should be boolean: {0}".format(value))

    @staticmethod
    def _aslimit(value):
        if isinstance(value, string_types):
            module = ast.parse(value)
            if isinstance(module, ast.Module) and len(module.body) == 1 and isinstance(module.body[0], ast.Expr):
                expr = module.body[0].value
                if isinstance(expr, ast.Num):
                    return expr.n

                elif isinstance(expr, ast.Name) and expr.id == "inf":
                    return femtocode.typesystem.inf

                elif isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
                    if isinstance(expr.operand, ast.Num):
                        return -expr.operand.n

                    elif isinstance(expr.operand, ast.Name) and expr.operand.id == "inf":
                        return -femtocode.typesystem.inf

                elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "almost" and len(expr.args) == 1 and len(expr.keywords) == 0 and expr.kwargs is None and expr.starargs is None:
                    if isinstance(expr.args[0], ast.Num):
                        return femtocode.typesystem.almost(expr.args[0].n)

                    elif isinstance(expr.args[0], ast.Name) and expr.args[0].id == "inf":
                        return femtocode.typesystem.almost(femtocode.typesystem.inf)

                    elif isinstance(expr.args[0], ast.UnaryOp) and isinstance(expr.args[0].op, ast.USub):
                        if isinstance(expr.args[0].operand, ast.Num):
                            return femtocode.typesystem.almost(-expr.args[0].operand.n)

                        elif isinstance(expr.args[0].operand, ast.Name) and expr.args[0].operand.id == "inf":
                            return femtocode.typesystem.almost(-femtocode.typesystem.inf)

            raise DatasetDeclaration.Error("couldn't parse as a min/max/least/most limit: {0}".format(value))

        elif isinstance(value, (int, long, float)):
            return value

        elif isinstance(value, femtocode.typesystem.almost) and isinstance(value.real, (int, long, float)):
            return value

        else:
            raise DatasetDeclaration.Error("unrecognized type for min/max/least/most limit: {0}".format(value))

    @staticmethod
    def _toschema(quantity):
        if quantity in ("boolean", "number", "real", "integer", "extended", "string", "collection", "vector", "matrix", "tensor", "record"):
            return DatasetDeclaration._toschema({"type": quantity})

        elif isinstance(quantity, dict):
            if quantity.get("type") == "boolean":
                return femtocode.typesystem.boolean

            elif quantity.get("type") == "number" or quantity.get("type") == "real":
                return femtocode.typesystem.Number(
                    min=DatasetDeclaration._aslimit(quantity.get("min", "almost(-inf)")),
                    max=DatasetDeclaration._aslimit(quantity.get("max", "almost(inf)")),
                    whole=DatasetDeclaration._asbool(quantity.get("whole", False)))

            elif quantity.get("type") == "integer":
                return femtocode.typesystem.Number(
                    min=DatasetDeclaration._aslimit(quantity.get("min", "almost(-inf)")),
                    max=DatasetDeclaration._aslimit(quantity.get("max", "almost(inf)")),
                    whole=DatasetDeclaration._asbool(quantity.get("whole", True)))

            elif quantity.get("type") == "extended":
                return femtocode.typesystem.Number(
                    min=DatasetDeclaration._aslimit(quantity.get("min", "-inf")),
                    max=DatasetDeclaration._aslimit(quantity.get("max", "inf")),
                    whole=DatasetDeclaration._asbool(quantity.get("whole", False)))

            elif quantity.get("type") == "string":
                return femtocode.typesystem.String(
                    charset=quantity.get("charset", "bytes"),
                    fewest=DatasetDeclaration._aslimit(quantity.get("fewest", 0)),
                    most=DatasetDeclaration._aslimit(quantity.get("most", "almost(inf)")))

            elif quantity.get("type") == "collection":
                return femtocode.typesystem.Collection(
                    items=DatasetDeclaration._toschema(quantity.get("items")),
                    fewest=DatasetDeclaration._aslimit(quantity.get("fewest", 0)),
                    most=DatasetDeclaration._aslimit(quantity.get("most", "almost(inf)")))

            elif quantity.get("type") in ("vector", "matrix", "tensor"):
                dimensions = str(quantity.get("dimensions", ""))
                dimensions = re.split(r"\s*,\s*", dimensions.strip())
                for i, x in enumerate(dimensions):
                    try:
                        dimensions[i] = int(dimensions[i])
                    except ValueError:
                        raise DatasetDeclaration.Error("dimensions must be comma-separated integers")
                    
                if quantity["type"] == "vector":
                    if len(dimensions) != 1:
                        raise DatasetDeclaration.Error("vectors should have exactly one dimension")
                    return femtocode.typesystem.vector(
                        DatasetDeclaration._toschema(quantity.get("items")),
                        *dimensions)

                elif quantity["type"] == "matrix":
                    if len(dimensions) != 2:
                        raise DatasetDeclaration.Error("matrices should have exactly two dimensions")
                    return femtocode.typesystem.matrix(
                        DatasetDeclaration._toschema(quantity.get("items")),
                        *dimensions)

                elif quantity["type"] == "tensor":
                    if len(dimensions) <= 2:
                        raise DatasetDeclaration.Error("tensors should have more than two dimensions")
                    return femtocode.typesystem.tensor(
                        DatasetDeclaration._toschema(quantity.get("items")),
                        *dimensions)

            elif quantity.get("type") == "record":
                fields = quantity.get("fields")
                if not isinstance(fields, dict):
                    raise DatasetDeclaration.Error("record needs a fields, and that must be a mapping")
                return femtocode.typesystem.record(**dict((k, DatasetDeclaration._toschema(v)) for k, v in fields.items()))

            else:
                raise DatasetDeclaration.Error("type specification not recognized or not supported for ROOT extraction: type {0}, keys {1}".format(quantity.get("type"), ", ".join(sorted(set(quantity.keys()).difference(set(["type"]))))))

        else:
            raise DatasetDeclaration.Error("type specification must be a string or dict: {0}".format(quantity))

    class Source(object):
        @staticmethod
        def fromJson(source):
            DatasetDeclaration._unrecognized(source.keys(), ["format", "paths"], "dataset declaration source")

            format = source["format"]
            if not isinstance(format, string_types):
                raise DatasetDeclaration.Error("dataset declaration source needs a name, and that name must be a string")

            paths = source.get("paths", [])
            if not isinstance(paths, (list, tuple)) or not all(isinstance(x, string_types) for x in paths):
                raise DatasetDeclaration.Error("dataset declaration source path must be a list of strings (denoted with '-' in YAML)")

            return DatasetDeclaration.Source(format, paths)

        def __init__(self, format, paths):
            if len(paths) == 0:
                raise DatasetDeclaration.Error("dataset declaration source path is empty")
            self.format = format
            self.paths = paths

        def __repr__(self):
            return "DatasetDeclaration.Source({0}, [{1}])".format(json.dumps(self.format), ", ".join(json.dumps(x) for x in self.paths))

    class Quantity(object):
        @staticmethod
        def fromJson(quantity, sources):
            tpe = quantity.get("type")
            if not isinstance(tpe, string_types):
                raise DatasetDeclaration.Error("dataset declaration quantity needs a type, and that must be a string")

            if "alias" in quantity:
                raise DatasetDeclaration.Error("datasets from ROOT do not support recursive types, so the 'alias' keyword is not allowed")

            if tpe == "boolean":
                DatasetDeclaration._unrecognized(quantity.keys(), ["from"], "boolean type")
                frm = DatasetDeclaration.Primitive.fromJson(quantity.get("from"), sources)
                return DatasetDeclaration.Primitive(DatasetDeclaration._toschema(quantity), frm)


# boolean
# number: min max whole
# integer: min max
# real: min max
# extended: min max
# string: charset (only bytes), fewest, most
# collection: items, fewest, most, ordered
# vector: items, dimensions
# matrix: items, dimensions
# tensor: items, dimensions
# record: fields




    class Structure(Quantity):
        def __init__(self):
            pass

    class Primitive(Quantity):
        def __init__(self):
            pass

    @staticmethod
    def fromYamlString(declaration):
        return DatasetDeclaration.fromJson(strictyaml.load(declaration))

    @staticmethod
    def fromJsonString(declaration):
        return DatasetDeclaration.fromJson(json.loads(declaration))

    @staticmethod
    def fromJson(declaration):
        def resolve(obj, definitions, defining):
            if isinstance(obj, string_types):
                if obj in definitions:
                    if definitions[obj] == defining:
                        raise DatasetDeclaration.Error("definitions in dataset declaration must not be recursively defined (in \"{0}\")".format(defining))
                    return resolve(definitions[obj], definitions, defining)
                else:
                    return obj

            elif isinstance(obj, dict):
                if any(not isinstance(k, string_types) for k in obj.keys()):
                    raise DatasetDeclaration.Error("mapping keys in dataset declaration must be strings ({0})".format(json.dumps(k)))
                return dict((k, resolve(v, definitions, defining)) for k, v in obj.items())

            elif isinstance(obj, (list, tuple)):
                return [resolve(x, definitions, defining) for x in obj]

            elif obj is True or obj is False or obj is None:
                return obj

            else:
                raise DatasetDeclaration.Error("unrecognized object in dataset declaration: {0}".format(obj))

        if not isinstance(declaration, dict):
            raise DatasetDeclaration.Error("dataset declaration must be a dict (after parsing JSON or YAML)")

        DatasetDeclaration._unrecognized(declaration.keys(), ["define", "name", "source", "schema"], "dataset declaration")

        definitions = declaration.get("define", {})
        if not isinstance(definitions, dict):
            raise DatasetDeclaration.Error("dataset definitions must be a dict: {0}".format(definitions))
        for k in definitions.keys():
            definitions[k] = resolve(definitions[k], definitions, k)

        if not isinstance(declaration.get("name"), string_types):
            raise DatasetDeclaration.Error("dataset declaration needs a name, and that name must be a string")
        name = declaration["name"]   # never expand it, even if it coincides with a definition

        source = declaration.get("source", [])
        if not isinstance(source, (list, tuple)):
            raise DatasetDeclaration.Error("dataset declaration source must be a list (denoted with '-' in YAML)")
        source = [DatasetDeclaration.Source.fromJson(resolve(x, definitions, None)) for x in source]

        fields = declaration.get("schema")
        if not isinstance(fields, dict):
            raise DatasetDeclaration.Error("dataset declaration fields must be a mapping (no '-' in YAML)")
        fields = dict((k, resolve(v, definitions, None)) for k, v in fields.items())

        return DatasetDeclaration(name, source, **fields)

    def __init__(self, name, source, **fields):
        self.name = name
        self.source = source
        self.fields = fields

    def __repr__(self):
        return "DatasetDeclaration({0}, {1}, {2})".format(json.dumps(self.name), repr(self.source), ", ".join("{0}={1}".format(k, repr(v)) for k, v in self.fields.items()))

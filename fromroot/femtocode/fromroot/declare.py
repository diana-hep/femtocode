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

import json
import glob
import re
from femtocode.py23 import *
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from femtocode.typesystem import *

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

    class Source(object):
        @staticmethod
        def fromJson(source):
            format = source["format"]
            if not isinstance(format, string_types):
                raise DatasetDeclaration.Error("dataset declaration source needs a name, and that name must be a string")

            paths = source.get("paths", [])
            if not isinstance(paths, (list, tuple)) or not all(isinstance(x, string_types) for x in paths):
                raise DatasetDeclaration.Error("dataset declaration source path must be a list of strings (denoted with '-' in YAML)")

            return DatasetDeclaration.Source(format, paths)

        def __init__(self, format, paths):
            self.format = format
            self.paths = paths

        def __repr__(self):
            return "DatasetDeclaration.Source({0}, [{1}])".format(json.dumps(self.format), ", ".join(json.dumps(x) for x in self.paths))

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







# boolean
# integer: min max
# real: min max
# extended: min max
# string: charset (only bytes), fewest, most

# collection: items, fewest, most, ordered
# vector: items, dimensions
# matrix: items, dimensions
# tensor: items, dimensions
# record: fields






# def _filesFromPath(path):
#     # FIXME: move this to a C function to remove dependence on PyROOT and therefore Python 2
#     import ROOT
#     for x in ROOT.TSystemDirectory(path, path).GetListOfFiles():
#         yield x.GetName()

# def filteredFilesFromPath(path, filter):
#     for x in _filesFromPath(path):
#         if glob.fnmatch.fnmatch(x, filter):
#             yield path.rstrip("/") + "/" + x

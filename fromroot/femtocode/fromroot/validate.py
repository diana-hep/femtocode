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

import glob
import re
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from femtocode.fromroot.dataset import *
from femtocode.fromroot.declare import DatasetDeclaration
from femtocode.fromroot._fastreader import fillarrays

def filesFromPath(path):
    url = urlparse(path)
    if url.scheme == "":
        for x in glob.glob(url.path):
            yield x

    elif url.scheme == "root":
        if "**" in url.path:
            raise NotImplementedError("double-star wildcards (**) not supported in XRootD")
        if "{" in url.path or "}" in url.path:
            raise NotImplementedError("curly braces ({ and }) not supported in XRootD")

        import XRootD.client
        fs = XRootD.client.FileSystem("{0}://{1}".format(url.scheme, url.netloc))

        def exists(fullpath):
            status, dummy = fs.stat(fullpath)
            if status.status == 3 and status.code == 204:
                raise IOError("Could not connect to {0}://{1}: {2}".format(url.scheme, url.netloc, status.message))
            return status.ok

        def search(path, patterns):
            fullpath = "/" + "".join("/" + x for x in path)

            if len(patterns) > 0 and re.search(r"[\*\?\[\]]", patterns[0]) is None:
                if exists(fullpath + "/" + patterns[0]):
                    for x in search(path + [patterns[0]], patterns[1:]):
                        yield x

            else:
                status, listing = fs.dirlist(fullpath)
                if status.status == 3 and status.code == 204:
                    raise IOError("Could not connect to {0}://{1}: {2}".format(url.scheme, url.netloc, status.message))
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

def sanityCheck(quantity, collectionDepth=0):
    if isinstance(quantity, DatasetDeclaration):
        for x in quantity.fields.values():
            sanityCheck(x, collectionDepth)

    elif isinstance(quantity, DatasetDeclaration.Collection):
        sanityCheck(quantity.items, collectionDepth + 1)

    elif isinstance(quantity, DatasetDeclaration.Record):
        for name, field in quantity.fields.items():
            sanityCheck(field, collectionDepth)

    elif isinstance(quantity, DatasetDeclaration.Primitive):
        if quantity.frm.size is None and collectionDepth != 0:
            raise DatasetDeclaration.Error(quantity.lc, "field has no declared 'size' but it is nested within a collection")
        elif quantity.frm.size is not None and collectionDepth == 0:
            raise DatasetDeclaration.Error(quantity.lc, "field has a 'size' attribute but it is not nested within a collection")

def getPaths(quantity):
    if isinstance(quantity, DatasetDeclaration):
        for x in quantity.fields.values():
            for y in getPaths(x):
                yield y

    elif isinstance(quantity, DatasetDeclaration.Collection):
        for x in getPaths(quantity.items):
            yield x

    elif isinstance(quantity, DatasetDeclaration.Record):
        for field in quantity.fields.values():
            for x in getPaths(field):
                yield x

    elif isinstance(quantity, DatasetDeclaration.Primitive):
        for source in quantity.frm.sources:
            for path in source.paths:
                yield (path, source.tree)

    else:
        assert False, "expected either a DatasetDeclaration or a Quantity"

def getBranchesForPaths(quantity, paths):
    if isinstance(quantity, DatasetDeclaration):
        for x in quantity.fields.values():
            getBranchesForPaths(x, paths)

    elif isinstance(quantity, DatasetDeclaration.Collection):
        getBranchesForPaths(quantity.items, paths)

    elif isinstance(quantity, DatasetDeclaration.Record):
        for field in quantity.fields.values():
            getBranchesForPaths(field, paths)

    elif isinstance(quantity, DatasetDeclaration.Primitive):
        for source in quantity.frm.sources:
            for path in source.paths:
                paths[(path, source.tree)].append((quantity.frm.data, quantity.frm.size))

def assignFilesToSegments(quantity, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name=None)
    if isinstance(quantity, DatasetDeclaration):
        for k, v in quantity.fields.items():
            assignFilesToSegments(v, filesToNumEntries, fileColumnsToLengths, pathsToFiles, k)

    elif isinstance(quantity, DatasetDeclaration.Collection):
        assignFilesToSegments(quantity.items, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name)

    elif isinstance(quantity, DatasetDeclaration.Record):
        for k, v in quantity.fields.items():
            assignFilesToSegments(v, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name, name + "." + k)

        # FIXME: and then check

    elif isinstance(quantity, DatasetDeclaration.Primitive):
        segments = []

        group = 0
        index = 0
        for source in primitive.frm.sources:
            for path in source.paths:
                for file in pathsToFiles[(path, source.tree)]:
                    numEntries = filesToNumEntries[(file, source.tree)]
                    if quantity.frm.size is None:
                        dataLength = numEntries
                    else:
                        dataLength = fileColumnsToLengths[(file, source.tree, primitive.frm.data)]

                    if index == 0:
                        segments.append(ROOTSegment(
                            quantity.frm.data,
                            dataLength,
                            quantity.frm.dtype,
                            quantity.frm.size,
                            numEntries))
                    else:
                        segments[-1].dataLength += dataLength
                        segments[-1].numEntries += numEntries

                    index += 1
                    if index > source.groupsize:
                        index = 0
                        group += 1

        # HERE!!! Return it somehow!

                        
    else:
        assert False, "expected either a DatasetDeclaration or a Quantity"

################################################################################

declaration = DatasetDeclaration.fromYamlString(declaration)

sanityCheck(declaration)

pathsToFiles = {}
for path, tree in set(getPaths(declaration)):
    pathsToFiles[(path, tree)] = []
    for file in filesFromPath(path):
        pathsToFiles[(path, tree)].append(file)

pathsToBranches = dict((x, []) for x in pathsToFiles)
getBranchesForPaths(declaration, pathsToBranches)

filesToNumEntries = {}
fileColumnsToLengths = {}
for (path, tree), files in pathsToFiles.items():
    for file in files:
        sizeToData = {}
        for dataName, sizeName in pathsToBranches[(path, tree)]:
            if sizeName is not None:
                sizeToData[sizeName] = dataName   # get rid of duplicate sizeNames

        dataSizeNoDuplicates = [(dataName, sizeName) for sizeName, dataName in sizeToData.items()]

        lengths = fillarrays(file, tree, [(dataName, sizeName, None, None) for dataName, sizeName in dataSizeNoDuplicates])
        filesToNumEntries[(file, tree)] = int(lengths[0])
        for (dataName, sizeName), length in zip(dataSizeNoDuplicates, lengths[1:]):
            fileColumnsToLengths[(file, tree, dataName)] = int(length)

groups = assignFilesToSegments(declaration, filesToNumEntries, fileColumnsToLengths, pathsToFiles)

dataset = ROOTDataset(
    declaration.name,
    dict((k, v.schema) for k, v in declaration.fields.items()),
    [])



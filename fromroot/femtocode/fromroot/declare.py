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

import strictyaml

def filesFromPath(path):
    url = urlparse(path)
    if url.scheme == "":
        for x in glob.glob(url.path):
            yield x

    elif url.scheme == "root":
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




## class DatasetDefinition(object):
    









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

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
import XRootD.client
from XRootD.client.flags import OpenFlags

def filesFromPath(path):
    url = urlparse(path)
    if url.scheme != "":
        fs = XRootD.client.FileSystem(url.scheme + "://" + url.netloc)

        def exists(path):
            return fs.locate(path, OpenFlags.NONE)[0].ok

        def search(path):
            status, listing = fs.dirlist(path)
            if status.ok:
                for x in listing.dirlist:
                    for y in search(path.rstrip("/") + "/" + x.name):
                        yield y
            else:
                yield path

        m = re.match(r"(^[^\?\*\[\]\{\}]*/).*[\?\*\[\]\{\}].*", url.path)
        if m is None:
            path = url.path
        else:
            path = m.group(1)

        for x in search(path):
            if m is None or glob.fnmatch.fnmatchcase(x, url.path):
                yield url.scheme + "://" + url.netloc + x

    else:
        for x in glob.glob(url.path):
            yield x




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

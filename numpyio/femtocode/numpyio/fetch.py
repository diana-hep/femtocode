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
import struct
import threading
import zipfile
try:
    from urllib2 import urlparse
    urlparse = urlparse.urlparse
except ImportError:
    from urllib.parse import urlparse

import numpy

from femtocode.py23 import *
from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.execution import ExecutionFailure
from femtocode.run.compute import DataAddress
from femtocode.run.cache import CacheOccupant
from femtocode.numpyio.xrootd import XRootDReader

class NumpyFetcher(threading.Thread):
    chunksize = 1024

    def __init__(self, occupants, workItem):
        super(NumpyFetcher, self).__init__()
        self.occupants = occupants
        self.workItem = workItem
        self.daemon = True

    def files(self, column):
        out = None
        if column.issize():
            for n, c in self.workItem.executor.query.dataset.columns.items():
                if c.size == column:
                    out = self.workItem.group.segments[n].files
                    break
        else:
            out = self.workItem.group.segments[column].files

        if out is None:
            out = self.workItem.group.files
        return out

    def run(self):
        try:
            filesToOccupants = {}

            for occupant in self.occupants:
                for fileName in self.files(occupant.address.column):
                    if fileName not in filesToOccupants:
                        filesToOccupants[fileName] = []
                    filesToOccupants[fileName].append(occupant)

            for fileName, occupants in filesToOccupants.items():
                protocol = urlparse(fileName).scheme
                if protocol == "":
                    zf = zipfile.ZipFile(open(fileName, "rb"))
                elif protocol == "root":
                    zf = zipfile.ZipFile(XRootDReader(fileName))
                else:
                    raise NotImplementedError

                for occupant in occupants:
                    stream = zf.open(str(occupant.address.column) + ".npy")
                    assert stream.read(6) == "\x93NUMPY"

                    version = struct.unpack("bb", stream.read(2))
                    if version[0] == 1:
                        headerlen, = struct.unpack("<H", stream.read(2))
                    else:
                        headerlen, = struct.unpack("<I", stream.read(4))

                    header = stream.read(headerlen)
                    headerdata = ast.literal_eval(header)

                    dtype = numpy.dtype(headerdata["descr"])
                    numBytes = reduce(lambda a, b: a * b, (dtype.itemsize,) + headerdata["shape"])

                    assert occupant.totalBytes == numBytes

                    readBytes = 0
                    while readBytes < numBytes:
                        size = min(self.chunksize, numBytes - readBytes)
                        readBytes += size
                        occupant.fill(stream.read(size))

                zf.close()

        except Exception as exception:
            for occupant in self.occupants:
                with occupant.lock:
                    occupant.fetchfailure = ExecutionFailure(exception, sys.exc_info()[2])

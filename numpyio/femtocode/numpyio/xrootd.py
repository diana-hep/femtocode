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

import os

class XRootDReader(object):
    def __init__(self, url):
        self.url = url

        import pyxrootd.client
        self.file = pyxrootd.client.File()
        status, dummy = self.file.open(self.url)
        if status["error"]:
            raise IOError(status.message)

        status, self.stat = self.file.stat()
        if status["error"]:
            raise IOError(status.message)

        self.size = self.stat["size"]
        self.pos = 0

    def read(self, size=None):
        if size is None:
            size = self.size - self.pos

        status, result = self.file.read(self.pos, size)
        if status["error"]:
            raise IOError(status.message)

        self.pos += len(result)
        return result

    def tell(self):
        return self.pos

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            self.pos = offset
        elif whence == os.SEEK_CUR:
            self.pos += offset
        elif whence == os.SEEK_END:
            self.pos = self.size + offset
        else:
            raise NotImplementedError(whence)

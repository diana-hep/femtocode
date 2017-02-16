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

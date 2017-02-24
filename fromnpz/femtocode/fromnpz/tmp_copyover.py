import os
import threading
try:
    from urllib import quote as urllib_quote
except ImportError:
    from urllib.parse import quote as urllib_quote

import numpy
import pycurl

class DataAddress(object):
    __slots__ = ("dataset", "column", "group")

    def __init__(self, dataset, column, group):
        self.dataset = dataset
        self.column = column
        self.group = group
        
    def __repr__(self):
        return "DataAddress({0}, {1}, {2})".format(self.dataset, self.column, self.group)

    def __eq__(self, other):
        return isinstance(other, DataAddress) and self.dataset == other.dataset and self.column == other.column and self.group == other.group

    def __hash__(self):
        return hash((DataAddress, self.dataset, self.column, self.group))

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

class FetchData(threading.Thread):
    @property
    def fills(self):
        raise NotImplementedError

class FetchDataXRDNumpy(FetchData):
    urlprefix = "root://cmseos.fnal.gov//store/user/pivarski/"    # FIXME
    fills = False

    @staticmethod
    def tourl(address):
        return "{0}/{1}/{2}.npz".format(FetchDataXRDNumpy.urlprefix, address.dataset, address.group)
        
    _numBytesCache = {}
    @staticmethod
    def numBytes(address):
        out = FetchDataXRDNumpy._numBytesCache.get(address)
        if out is None:
            xrdnpy = numpy.load(XRootDReader(FetchDataXRDNumpy.tourl(address)))
            for zipinfo in xrdnpy.zip.filelist:
                if zipinfo.filename == address.column + ".npy":
                    out = zipinfo.file_size      # an overestimate because it includes the (tiny) .npy header
                    break
            if out is None:
                raise IOError(address)
            FetchDataXRDNumpy._numBytesCache[address] = out
        return out

    def __init__(self, occupants):
        super(FetchDataXRDNumpy, self).__init__(name="FetchDataXRDNumpy([{0}])".format(", ".join(map(repr, occupants))))
        self.occupants = occupants
        self.daemon = True

    def __repr__(self):
        return "FetchDataXRDNumpy({0})".format(self.occupants)        

    def run(self):
        for occupant in self.occupants:
            xrdnpy = numpy.load(XRootDReader(FetchDataXRDNumpy.tourl(occupant.address)))
            occupant.rawarray = xrdnpy[occupant.address.column]
            occupant.dtype = occupant.rawarray.dtype

class FetchDataHTTP(FetchData):
    urlprefix = "file:/home/pivarski/diana/fermiscope/"    # FIXME
    fills = True

    @staticmethod
    def tourl(address):
        return FetchDataHTTP.urlprefix + urllib_quote("{0}-{1}-{2}".format(address.dataset, address.column, address.group))

    _numBytesCache = {}
    @staticmethod
    def numBytes(address):
        out = FetchDataHTTP._numBytesCache.get(address)
        if out is None:
            import os
            out = os.stat("/home/pivarski/diana/fermiscope/" + urllib_quote("{0}-{1}-{2}".format(address.dataset, address.column, address.group))).st_size    # FIXME
            FetchDataHTTP._numBytesCache[address] = out
        return out

    _dtypeCache = {}
    @staticmethod
    def dtype(address):
        out = FetchDataHTTP._dtypeCache.get(address)
        if out is None:
            out = numpy.float64
            FetchDataHTTP._dtypeCache[address] = out
        return out

    def __init__(self, occupants):
        super(FetchDataHTTP, self).__init__(name="FetchDataHTTP([{0}])".format(", ".join(map(repr, occupants))))
        self.occupants = occupants
        self.daemon = True

    def __repr__(self):
        return "FetchDataHTTP({0})".format(self.occupants)

    def run(self):
        multicurl = pycurl.CurlMulti()
        for occupant in self.occupants:
            singlecurl = pycurl.Curl()
            singlecurl.setopt(pycurl.URL, self.tourl(occupant.address))
            singlecurl.setopt(pycurl.WRITEFUNCTION, occupant.fill)
            multicurl.add_handle(singlecurl)
        multicurl.perform()

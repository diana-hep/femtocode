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
import math
import re
import sys

from femtocode.defs import FemtocodeError
from femtocode.parser import t_NAME
from femtocode.py23 import *
from femtocode.util import *

inf = float("inf")
pi = math.pi

class almost(float):
    """almost(x) -> open end of an interval

    Obeys open-closed arithmetic assuming that float(x) is the closed end of an interval.
    """

    @staticmethod
    def min(*args):
        if len(args) == 0:
            raise TypeError("almost.min() takes at least 1 argument")
        elif len(args) == 1:
            return args[0]
        elif len(args) == 2:
            a, b = args
            if a < b:
                return a
            elif b < a:
                return b
            elif not isinstance(a, almost):
                return a
            else:
                return b
        else:
            return almost.min(*((almost.min(args[0], args[1]),) + args[2:]))

    @staticmethod
    def max(*args):
        if len(args) == 0:
            raise TypeError("almost.max() takes at least 1 argument")
        elif len(args) == 1:
            return args[0]
        elif len(args) == 2:
            a, b = args
            if a > b:
                return a
            elif b > a:
                return b
            elif not isinstance(a, almost):
                return a
            else:
                return b
        else:
            return almost.max(*((almost.max(args[0], args[1]),) + args[2:]))
            
    @staticmethod
    def complement(a):
        if isinstance(a, almost):
            return a.real
        elif isinstance(a, (int, long, float)):
            return almost(a)
        else:
            raise TypeError

    def __eq__(self, other):
        if isinstance(other, almost):
            return self.real == other.real
        else:
            return False
    def __ne__(self, other):
        if isinstance(other, almost):
            return self.real != other.real
        else:
            return True
    def __hash__(self):
        return hash((None, self.real))

    def __repr__(self):
        return "almost(" + repr(self.real) + ")"
    def __str__(self):
        return "almost(" + str(self.real) + ")"

    def __abs__(self):
        return almost(abs(self.real))
    def __pos__(self):
        return self
    def __neg__(self):
        return almost(-self.real)

    def __add__(self, other):
        return almost(self.real + other)
    def __radd__(self, other):
        return almost(other + self.real)
    def __sub__(self, other):
        return almost(self.real - other)
    def __rsub__(self, other):
        return almost(other - self.real)
    def __mul__(self, other):
        return almost(self.real * other)
    def __rmul__(self, other):
        return almost(other * self.real)
    def __pow__(self, other):
        return almost(self.real**other)
    def __rpow__(self, other):
        return almost(other**self.real)

    def __div__(self, other):
        return almost(self.real / other)
    def __rdiv__(self, other):
        return almost(other / self.real)
    def __truediv__(self, other):
        return almost(1.0*self.real / other)
    def __rtruediv__(self, other):
        return almost(1.0*other / self.real)
    def __floordiv__(self, other):
        return almost(self.real // other)
    def __rfloordiv__(self, other):
        return almost(other // self.real)

    def __mod__(self, other):
        return almost(self.real % other)
    def __rmod__(self, other):
        return almost(other % self.real)
    def __divmod__(self, other):
        a, b = divmod(self.real, other)
        return (almost(a), almost(b))
    def __rdivmod__(self, other):
        a, b = divmod(other, self.real)
        return (almost(a), almost(b))

class Schema(Serializable):
    def __init__(self, alias=None):
        self.alias = alias
        if alias is None:
            self._aliases = set()
        elif isinstance(alias, string_types):
            self._aliases = set([(alias, self)])
        else:
            raise FemtocodeError("alias {0} must be None or a string".format(alias))

    def __repr__(self):
        return self._repr_memo(set())

    def _update_memo(self, memo):
        if self.alias is not None:
            if self.alias in memo:
                return self.alias
            else:
                memo.add(self.alias)
                return None
        else:
            return None

    def name(self, plural=False):
        if plural:
            return self.__class__.__name__ + "s"
        else:
            return self.__class__.__name__

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True
        elif isinstance(other, Schema):
            return self.order < other.order
        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.__class__ == other.__class__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __gt__(self, other):
        return self.__ge__(other) and not self.__eq__(other)

    def __hash__(self):
        return hash((self.order,))

    def __call__(self, alias=None):
        return self.__class__(alias)

    @staticmethod
    def _numtojson(obj):
        if obj.real == -inf:
            num = "-inf"
        elif obj.real == inf:
            num = "inf"
        elif round(obj.real) == obj.real:
            num = int(obj.real)
        else:
            num = obj.real

        if isinstance(obj, almost):
            return {"almost": num}
        else:
            return num

    @staticmethod
    def _numfromjson(obj, path):
        if isinstance(obj, dict) and len(obj) == 1 and "almost" in obj:
            if obj["almost"] == "-inf":
                return almost(-inf)
            elif obj["almost"] == "inf":
                return almost(inf)
            elif isinstance(obj["almost"], (int, long, float)):
                return almost(obj["almost"])
            else:
                raise FemtocodeError("Expected number, \"-inf\", \"inf\" or {{\"almost\": _}} at JSON{0}\n\n    found {1}".format(path, obj))

        elif isinstance(obj, (int, long, float) + string_types):
            if obj == "-inf":
                return -inf
            elif obj == "inf":
                return inf
            elif isinstance(obj, (int, long, float)):
                return obj
            else:
                raise FemtocodeError("Expected number, \"-inf\", \"inf\" or {{\"almost\": _}} at JSON{0}\n\n    found {1}".format(path, obj))

        else:
            raise FemtocodeError("Expected number, \"-inf\", \"inf\" or {{\"almost\": _}} at JSON{0}\n\n    found {1}".format(path, obj))

    @staticmethod
    def fromJson(obj):
        def build(obj, path):
            if obj is None:
                return null

            elif isinstance(obj, string_types):
                if obj == "impossible":
                    return impossible
                elif obj == "null":
                    return null
                elif obj == "boolean":
                    return boolean
                elif obj == "integer":
                    return integer
                elif obj == "extended":
                    return extended
                elif obj == "real":
                    return real
                elif obj == "string":
                    return string
                elif obj == "empty":
                    return empty
                else:
                    raise FemtocodeError("Expected name of concrete type at JSON{0}\n\n    found {1}".format(path, obj))

            elif isinstance(obj, dict):
                if len(obj) == 1 and "alias" in obj:
                    return obj["alias"]   # this is a placeholder, to be replaced in resolve (below)

                elif "type" in obj:
                    if obj["type"] in ("impossible", "null", "empty"):
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        if obj["type"] == "impossible":
                            return impossible(**kwds)
                        elif obj["type"] == "null":
                            return null(**kwds)
                        elif obj["type"] == "empty":
                            return empty(**kwds)

                    elif obj["type"] == "boolean":
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        if "just" in obj:
                            if obj["just"] is True or obj["just"] is False:
                                kwds["just"] = obj["just"]
                            elif obj["just"] is None:
                                pass
                            else:
                                raise FemtocodeError("Expected \"just\" for \"type\": \"{0}\" to be true, false, or null at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["just"])))
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "just"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        return boolean(**kwds)

                    elif obj["type"] in ("integer", "real", "extended"):
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        if "min" in obj:
                            kwds["min"] = Schema._numfromjson(obj["min"], path + "[\"min\"]")
                        if "max" in obj:
                            kwds["max"] = Schema._numfromjson(obj["max"], path + "[\"max\"]")
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "min", "max"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        try:
                            if obj["type"] == "integer":
                                return integer(**kwds)
                            elif obj["type"] == "real":
                                return real(**kwds)
                            elif obj["type"] == "extended":
                                return extended(**kwds)
                        except FemtocodeError as err:
                            raise FemtocodeError("Error in arguments for \"type\": \"{0}\" at JSON{1}\n\n    {2}".format(obj["type"], path, str(err)))

                    elif obj["type"] == "string":
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        if "charset" in obj:
                            if isinstance(obj["charset"], string_types):
                                kwds["charset"] = obj["charset"]
                            else:
                                raise FemtocodeError("Expected \"charset\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["charset"])))
                        if "fewest" in obj:
                            kwds["fewest"] = Schema._numfromjson(obj["fewest"], path + "[\"fewest\"]")
                        if "most" in obj:
                            kwds["most"] = Schema._numfromjson(obj["most"], path + "[\"most\"]")
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "charset", "fewest", "most"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        try:
                            return string(**kwds)
                        except FemtocodeError as err:
                            raise FemtocodeError("Error in arguments for \"type\": \"{0}\" at JSON{1}\n\n    {2}".format(obj["type"], path, str(err)))
                        
                    elif obj["type"] == "collection":
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        if "items" in obj:
                            kwds["items"] = build(obj["items"], path + "[\"items\"]")
                        else:
                            raise FemtocodeError("Expected \"items\" for \"type\": \"{0}\" at JSON{1}\n\n    found keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, obj.keys()))))
                        if "fewest" in obj:
                            kwds["fewest"] = Schema._numfromjson(obj["fewest"], path + "[\"fewest\"]")
                        if "most" in obj:
                            kwds["most"] = Schema._numfromjson(obj["most"], path + "[\"most\"]")
                        if "ordered" in obj:
                            if isinstance(obj["ordered"], bool):
                                kwds["ordered"] = obj["ordered"]
                            else:
                                raise FemtocodeError("Expected \"ordered\" for \"type\": \"{0}\" to be bool at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["ordered"])))
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "items", "fewest", "most", "ordered"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        try:
                            return collection(**kwds)
                        except FemtocodeError as err:
                            raise FemtocodeError("Error in arguments for \"type\": \"{0}\" at JSON{1}\n\n    {2}".format(obj["type"], path, str(err)))

                    elif obj["type"] in ("vector", "matrix", "tensor"):
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        if "items" in obj:
                            items = build(obj["items"], path + "[\"items\"]")
                        else:
                            raise FemtocodeError("Expected \"items\" for \"type\": \"{0}\" at JSON{1}\n\n    found keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, obj.keys()))))
                        if "dimensions" in obj:
                            if isinstance(obj["dimensions"], list):
                                if all(isinstance(x, int) for x in obj["dimensions"]):
                                    dimensions = obj["dimensions"]
                                else:
                                    raise FemtocodeError("Expected \"dimensions\" for \"type\": \"{0}\" to be an array of integers at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["dimensions"])))
                            else:
                                raise FemtocodeError("Expected \"dimensions\" for \"type\": \"{0}\" to be [...] at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["dimensions"])))
                        else:
                            raise FemtocodeError("Expected \"dimensions\" for \"type\": \"{0}\" at JSON{1}\n\n    found keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, obj.keys()))))
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "items", "dimensions"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        try:
                            if obj["type"] == "vector":
                                return vector(items, *dimensions, **kwds)
                            elif obj["type"] == "matrix":
                                return matrix(items, *dimensions, **kwds)
                            elif obj["type"] == "tensor":
                                return tensor(items, *dimensions, **kwds)
                        except FemtocodeError as err:
                            raise FemtocodeError("Error in arguments for \"type\": \"{0}\" at JSON{1}\n\n    {2}".format(obj["type"], path, str(err)))

                    elif obj["type"] == "record":
                        kwds = {}
                        if "alias" in obj:
                            if isinstance(obj["alias"], string_types):
                                kwds["alias"] = obj["alias"]
                            else:
                                raise FemtocodeError("Expected \"alias\" for \"type\": \"{0}\" to be string at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["alias"])))
                        if "fields" in obj:
                            if isinstance(obj["fields"], dict) and all(isinstance(x, string_types) for x in obj["fields"].keys()):
                                kwds["fields"] = dict((n, build(t, path + "[\"fields\"][" + json.dumps(n) + "]")) for n, t in obj["fields"].items())
                            else:
                                raise FemtocodeError("Expected \"fields\" for \"type\": \"{0}\" to be {{...}}} at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["fields"])))
                        else:
                            raise FemtocodeError("Expected \"fields\" for \"type\": \"{0}\" at JSON{1}\n\n    found keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, obj.keys()))))
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "fields"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        try:
                            return Record(**kwds)
                        except FemtocodeError as err:
                            raise FemtocodeError("Error in arguments for \"type\": \"{0}\" at JSON{1}\n\n    {2}".format(obj["type"], path, str(err)))

                    elif obj["type"] == "union":
                        if "possibilities" in obj:
                            if isinstance(obj["possibilities"], list):
                                possibilities = [build(t, path + "[{0}]".format(i)) for i, t in enumerate(obj["possibilities"])]
                            else:
                                raise FemtocodeError("Expected \"possibilities\" for \"type\": \"{0}\" to be [...] at JSON{1}\n\n    found {2}".format(obj["type"], path, json.dumps(obj["possibilities"])))
                        else:
                            raise FemtocodeError("Expected \"possibilities\" for \"type\": \"{0}\" at JSON{1}\n\n    found keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, obj.keys()))))
                        unexpected = set(obj.keys()).difference(set(["_id", "type", "alias", "possibilities"]))
                        if len(unexpected) > 0:
                            raise FemtocodeError("Unexpected keys for \"type\": \"{0}\" at JSON{1}\n\n    found unexpected keys {2}".format(obj["type"], path, ", ".join(map(json.dumps, unexpected))))
                        try:
                            return union(*possibilities)
                        except FemtocodeError as err:
                            raise FemtocodeError("Error in arguments for \"type\": \"{0}\" at JSON{1}\n\n    {2}".format(obj["type"], path, str(err)))
                    else:
                        raise FemtocodeError("Expected name of parameterized type at JSON{0}\n\n    found {1}".format(path, obj))

                else:
                    raise FemtocodeError("Expected \"type\" in {{...}} at JSON{0}\n\n    found keys {1}".format(path, ", ".join(map(json.dumps, obj.keys()))))

            else:
                raise FemtocodeError("Expected string or {{...}} at JSON{0}\n\n    found {1}".format(path, obj))

        out = build(obj, "")

        return resolve([out])[0]

    def toJson(self):
        return self._json_memo(set())

class Impossible(Schema):   # results in a compilation error
    order = 0

    def __init__(self, reason=None, alias=None):
        self.reason = reason
        super(Impossible, self).__init__(alias)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        if self.alias is not None:
            return "impossible(alias={0})".format(json.dumps(self.alias))
        else:
            return "impossible"

    def __contains__(self, other):
        return False

    def __call__(self, reason=None, alias=None):
        return self.__class__(self.reason if reason is None else reason, alias)

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        if self.alias is not None:
            return {"type": "impossible", "alias": self.alias}
        else:
            return "impossible"

# Primitive types would have no size column if they're not in a collection
class Primitive(Schema): pass

class Null(Primitive):
    order = 1

    def __init__(self, alias=None):
        super(Null, self).__init__(alias)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        if self.alias is not None:
            return "null(alias={0})".format(json.dumps(self.alias))
        else:
            return "null"

    def __contains__(self, other):
        return isinstance(other, Null) or other is None

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        if self.alias is not None:
            return {"type": "null", "alias": self.alias}
        else:
            return "null"

class Boolean(Primitive):
    order = 2

    def __init__(self, just=None, alias=None):
        self.just = just
        super(Boolean, self).__init__(alias)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        args = []
        if self.just is not None:
            args.append("just={0}".format(repr(self.just)))
        if self.alias is not None:
            args.append("alias={0}".format(json.dumps(self.alias)))

        if len(args) > 0:
            return "boolean({0})".format(", ".join(args))
        else:
            return "boolean"

    def __contains__(self, other):
        if isinstance(other, Boolean):
            if other.just is True:
                return self.just is None or self.just is True
            elif other.just is False:
                return self.just is None or self.just is False
            else:
                return self.just is None

        else:
            if other is True:
                return self.just is None or self.just is True
            elif other is False:
                return self.just is None or self.just is False
            else:
                return False

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True

        elif isinstance(other, Schema):
            if self.order == other.order:
                return self.just < other.just
            else:
                return self.order < other.order

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.__class__ == other.__class__ and self.just == other.just

    def __hash__(self):
        return hash((self.order, self.just))

    def __call__(self, just=(), alias=None):
        return self.__class__(self.just if just == () else just, alias)

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        args = {}
        if self.just is not None:
            args["just"] = self.just
        if self.alias is not None:
            args["alias"] = self.alias

        if len(args) > 0:
            args["type"] = "boolean"
            return args
        else:
            return "boolean"

class Number(Primitive):
    order = 3

    _floatNaN = float("nan")
    _intNaN = 9221120237041090560   # byte-for-byte equivalent of float("nan")
                                    # numpy.array([float("nan")], dtype=">f8").view(">i8")[0]
                                    # numpy.array([float("nan")], dtype="<f8").view("<i8")[0]
                                    # 99.975% of the maximum possible value: 9223372036854775807

    def __init__(self, min=almost(-inf), max=almost(inf), whole=False, alias=None):
        if not isinstance(min, (int, long, float)):
            raise FemtocodeError("Number min ({0}) must be a number (or an almost(number))".format(min))
        if not isinstance(max, (int, long, float)):
            raise FemtocodeError("Number max ({0}) must be a number (or an almost(number))".format(max))
        if not isinstance(whole, bool):
            raise FemtocodeError("Number whole ({0}) must be bool".format(whole))

        if not isinstance(min, almost) and not isinstance(max, almost) and min == max and not math.isinf(min) and round(min) == min:
            whole = True

        if whole:
            if min == -inf:
                raise FemtocodeError("for whole Number intervals, min ({0}) cannot be -inf; try almost(-inf)".format(min))
            if max == inf:
                raise FemtocodeError("for whole Number intervals, max ({0}) cannot be inf; try almost(inf)".format(max))
            if min != almost(-inf):
                if isinstance(min, almost) and round(min.real) == min.real:
                    min = min.real + 1
                if round(min.real) != min.real:
                    min = math.ceil(min)
                min = int(min)
            if max != almost(inf):
                if isinstance(max, almost) and round(max.real) == max.real:
                    max = max.real - 1
                if round(max.real) != max.real:
                    max = math.floor(max)
                max = int(max)
        else:
            if isinstance(min, almost):
                min = almost(float(min.real))
            else:
                min = float(min)
            if isinstance(max, almost):
                max = almost(float(max.real))
            else:
                max = float(max)

        if min > max:
            raise FemtocodeError("Number min ({0}) must not be greater than max ({1}){2}".format(min, max, " after adjustments for whole-numbered interval" if whole else ""))
        if min.real == max.real and (isinstance(min, almost) or isinstance(max, almost)):
            raise FemtocodeError("Number min ({0}) and max ({1}) may only be equal to one another if they are closed endpoints (not almost(endpoint))".format(min, max))

        # get rid of negative zeros (for display reasons)
        if min == 0: min = 0
        elif min == almost(0): min = almost(0)
        if max == 0: max = 0
        elif max == almost(0): max = almost(0)

        self.min = min
        self.max = max
        self.whole = whole
        super(Number, self).__init__(alias)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        if self.whole and self.min == almost(-inf) and self.max == almost(inf):
            base = "integer"
            args = []
        elif self.whole:
            base = "integer"
            args = ["min={0}".format(self.min), "max={0}".format(self.max)]
        elif self.min == -inf and self.max == inf:
            base = "extended"
            args = []
        elif self.min == -inf or self.max == inf:
            base = "extended"
            args = ["min={0}".format(self.min), "max={0}".format(self.max)]
        elif self.min == almost(-inf) and self.max == almost(inf):
            base = "real"
            args = []
        else:
            base = "real"
            args = ["min={0}".format(self.min), "max={0}".format(self.max)]

        if self.alias is not None:
            args.append("alias={0}".format(json.dumps(self.alias)))

        if len(args) == 0:
            return base
        else:
            return "{0}({1})".format(base, ", ".join(args))

    def __contains__(self, other):
        if isinstance(other, Number):
            return almost.min(self.min, other.min) == self.min and \
                   almost.max(self.max, other.max) == self.max and \
                   (not self.whole or other.whole or (other.min == other.max and round(other.min) == other.min))

        elif isinstance(other, Schema):
            return False

        elif isinstance(other, (int, long, float)):
            if math.isnan(other):
                return False
            else:
                return almost.min(self.min, other) == self.min and \
                       almost.max(self.max, other) == self.max and \
                       (not self.whole or round(other) == other)

        else:
            return False

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True

        elif isinstance(other, Schema):
            if self.order == other.order:
                if self.min == other.min:
                    if self.max == other.max:
                        return self.whole < other.whole
                    else:
                        return self.max < other.max
                else:
                    return self.min < other.min
            else:
                return self.order < other.order

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.__class__ == other.__class__ and \
               self.min == other.min and \
               self.max == other.max and \
               self.whole == other.whole

    def __hash__(self):
        return hash((self.order, self.min, self.max, self.whole))

    def __call__(self, min=None, max=None, whole=None, alias=None):
        return self.__class__(self.min if min is None else min,
                              self.max if max is None else max,
                              self.whole if whole is None else whole,
                              alias)

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        if self.whole and self.min == almost(-inf) and self.max == almost(inf):
            out = {"type": "integer"}
        elif self.whole:
            out = {"type": "integer", "min": Schema._numtojson(self.min), "max": Schema._numtojson(self.max)}
        elif self.min == -inf and self.max == inf:
            out = {"type": "extended"}
        elif self.min == -inf or self.max == inf:
            out = {"type": "extended", "min": Schema._numtojson(self.min), "max": Schema._numtojson(self.max)}
        elif self.min == almost(-inf) and self.max == almost(inf):
            out = {"type": "real"}
        else:
            out = {"type": "real", "min": Schema._numtojson(self.min), "max": Schema._numtojson(self.max)}

        if self.alias is not None:
            out["alias"] = self.alias

        if len(out) == 1:
            return out["type"]
        else:
            return out

class String(Schema):
    order = 4

    def __init__(self, charset="bytes", fewest=0, most=almost(inf), alias=None):
        if charset not in ("bytes", "unicode"):
            raise FemtocodeError("String charset {0} not recognized".format(json.dumps(charset)))
        if not (isinstance(fewest, (int, long, float)) and not isinstance(fewest, almost) and fewest >= 0 and round(fewest) == fewest):
            raise FemtocodeError("String fewest ({0}) must be a nonnegative integer".format(fewest))
        if not (isinstance(most, (int, long, float)) and (most == almost(inf) or (not isinstance(most, almost) and round(most) == most))):
            raise FemtocodeError("String most ({0}) must be an integer or almost(inf)".format(most))
        if fewest > most:
            raise FemtocodeError("String fewest ({0}) must not be greater than most ({1})".format(fewest, most))

        self.charset = charset
        self.fewest = int(fewest)
        self.most = int(most) if most != almost(inf) else most
        super(String, self).__init__(alias)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        args = []
        if self.charset != "bytes":
            args.append("{0}".format(json.dumps(self.charset)))
        if not self.fewest == 0:
            args.append("fewest={0}".format(self.fewest))
        if not self.most == almost(inf):
            args.append("most={0}".format(self.most))
        if self.alias is not None:
            args.append("alias={0}".format(json.dumps(self.alias)))

        if len(args) == 0:
            return "string"
        else:
            return "string({0})".format(", ".join(args))

    def __contains__(self, other):
        if isinstance(other, String):
            return self.charset == other.charset and \
                   integer(other.fewest, other.most) in integer(self.fewest, self.most)

        elif isinstance(other, string_types):
            ok = False
            if sys.version_info[0] >= 3:
                if self.charset == "bytes" and isinstance(other, bytes):
                    ok = True
                if self.charset == "unicode" and isinstance(other, str):
                    ok = True
            else:
                if self.charset == "bytes" and isinstance(other, str):
                    ok = True
                if self.charset == "unicode" and isinstance(other, unicode):
                    ok = True

            return ok and (self.fewest <= len(other) <= self.most)

        else:
            return False

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True

        elif isinstance(other, Schema):
            if self.order == other.order:
                if self.charset == other.charset:
                    if self.fewest == other.fewest:
                        return self.most < other.most
                    else:
                        return self.fewest < other.fewest
                else:
                    return self.charset < other.charset
            else:
                return self.order < other.order

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self.charset == other.charset and \
               self.fewest == other.fewest and \
               self.most == other.most

    def __hash__(self):
        return hash((self.order, self.charset, self.fewest, self.most))

    def __call__(self, charset=None, fewest=None, most=None, alias=None):
        return self.__class__(self.charset if charset is None else charset,
                              self.fewest if fewest is None else fewest,
                              self.most if most is None else most,
                              alias)

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        out = {}
        if self.charset != "bytes":
            out["charset"] = self.charset
        if not self.fewest == 0:
            out["fewest"] = Schema._numtojson(self.fewest)
        if not self.most == almost(inf):
            out["most"] = Schema._numtojson(self.most)
        if self.alias is not None:
            out["alias"] = self.alias

        if len(out) == 0:
            return "string"
        else:
            out["type"] = "string"
            return out

class Collection(Schema):
    order = 5

    def __init__(self, items, fewest=0, most=almost(inf), ordered=False, alias=None):
        if not isinstance(items, (Schema,) + string_types):
            raise FemtocodeError("Collection items ({0}) must be a Schema or an alias string".format(items))
        if not (isinstance(fewest, (int, long, float)) and not isinstance(fewest, almost) and fewest >= 0 and round(fewest) == fewest):
            raise FemtocodeError("Collection fewest ({0}) must be a nonnegative integer".format(fewest))
        if not (isinstance(most, (int, long, float)) and (most == almost(inf) or (not isinstance(most, almost) and round(most) == most))):
            raise FemtocodeError("Collection most ({0}) must be an integer or almost(inf)".format(most))
        if fewest > most:
            raise FemtocodeError("Collection fewest ({0}) must not be greater than most ({1})".format(fewest, most))
        if not isinstance(ordered, bool):
            raise FemtocodeError("Collection ordered ({0}) must be bool".format(ordered))

        if most == 0:
            self.items = null
            self.fewest = int(fewest)
            self.most = 0
            self.ordered = True
        else:
            self.items = items
            self.fewest = int(fewest)
            self.most = int(most) if most != almost(inf) else most
            self.ordered = ordered

        super(Collection, self).__init__(alias)

        if most == 0:
            # we drop items if most == 0, but don't lose its aliases
            def getaliases(x):
                if isinstance(x, Schema):
                    self._aliases.update(x._aliases)
                if isinstance(x, Collection):
                    getaliases(x.items)
                elif isinstance(x, Record):
                    for t in x.fields.values():
                        getaliases(t)
                elif isinstance(x, Union):
                    for p in x.possibilities:
                        getaliases(p)
            getaliases(items)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        if self.most == 0:
            if self.alias is None:
                return "empty"
            else:
                return "empty(alias={0})".format(json.dumps(self.alias))

        def generic():
            args = [self.items._repr_memo(memo) if isinstance(self.items, Schema) else repr(self.items)]
            if self.fewest != 0:
                args.append("fewest={0}".format(self.fewest))
            if self.most != almost(inf):
                args.append("most={0}".format(self.most))
            if self.ordered:
                args.append("ordered={0}".format(self.ordered))
            if self.alias is not None:
                args.append("alias={0}".format(json.dumps(self.alias)))
            return "collection({0})".format(", ".join(args))

        dimensions = []
        items = self
        while isinstance(items, Collection) and items.ordered and items.fewest == items.most and items.fewest != 0:
            if not items.ordered:
                return generic()
            dimensions.append(items.fewest)
            items = items.items

        args = list(map(repr, dimensions))
        if self.alias is not None:
            args.append("alias={0}".format(json.dumps(self.alias)))

        if len(dimensions) == 1:
            return "vector({0}, {1})".format(items._repr_memo(memo) if isinstance(items, Schema) else repr(items), ", ".join(args))
        elif len(dimensions) == 2:
            return "matrix({0}, {1})".format(items._repr_memo(memo) if isinstance(items, Schema) else repr(items), ", ".join(args))
        elif len(dimensions) > 2:
            return "tensor({0}, {1})".format(items._repr_memo(memo) if isinstance(items, Schema) else repr(items), ", ".join(args))
        else:
            return generic()
        
    def __contains__(self, other):
        if isinstance(other, Collection):
            ok = True
            if self.ordered:
                ok = ok and other.ordered               # ordered is more specific than unordered

            ok = ok and integer(other.fewest, other.most) in integer(self.fewest, self.most)

            if self.most == 0 or other.most == 0:
                return ok
            else:
                # contents only matter if either of the collections can be nonempty
                return ok and other.items in self.items
            
        elif isinstance(other, (list, tuple, set)):
            ok = True
            if self.ordered:
                ok = ok and isinstance(other, (list, tuple))

            ok = ok and self.fewest <= len(other) <= self.most

            return ok and all(x in self.items for x in other)

        else:
            return False

    def _items(self):
        if isinstance(self.items, Schema) and self.items.alias is not None:
            return self.items.alias
        else:
            return self.items

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True

        elif isinstance(other, Schema):
            if self.order == other.order:
                if self._items() == other._items():
                    if self.fewest == other.fewest:
                        if self.most == other.most:
                            return self.ordered < other.ordered
                        else:
                            return self.most < other.most
                    else:
                        return self.fewest < other.fewest
                else:
                    return self._items() < other._items()
            else:
                return self.order < other.order

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self._items() == other._items() and \
               self.fewest == other.fewest and \
               self.most == other.most and \
               self.ordered == other.ordered

    def __hash__(self):
        return hash((self.order, self._items(), self.fewest, self.most, self.ordered))

    def __call__(self, items=None, fewest=None, most=None, ordered=None, alias=None):
        return self.__class__(self.items if items is None else items,
                              self.fewest if fewest is None else fewest,
                              self.most if most is None else most,
                              self.ordered if ordered is None else ordered,
                              alias)

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        if self.most == 0:
            if self.alias is None:
                return "empty"
            else:
                return {"type": "empty", "alias": self.alias}

        def generic():
            out = {"type": "collection", "items": self.items._json_memo(memo)}
            if self.fewest != 0:
                out["fewest"] = Schema._numtojson(self.fewest)
            if self.most != almost(inf):
                out["most"] = Schema._numtojson(self.most)
            if self.ordered:
                out["ordered"] = self.ordered
            if self.alias is not None:
                out["alias"] = self.alias
            return out

        dimensions = []
        items = self
        while isinstance(items, Collection) and items.ordered and items.fewest == items.most and items.fewest != 0:
            if not items.ordered:
                return generic()
            dimensions.append(items.fewest)
            items = items.items

        out = {"dimensions": dimensions}
        if self.alias is not None:
            out["alias"] = self.alias

        if len(dimensions) == 1:
            out["type"] = "vector"
            out["items"] = items._json_memo(memo)
            return out
        elif len(dimensions) == 2:
            out["type"] = "matrix"
            out["items"] = items._json_memo(memo)
            return out
        elif len(dimensions) > 2:
            out["type"] = "tensor"
            out["items"] = items._json_memo(memo)
            return out
        else:
            return generic()

class Record(Schema):
    order = 6

    def __init__(self, fields, alias=None):
        if not isinstance(fields, dict):
            raise FemtocodeError("Record fields ({0}) must be a dictionary".format(fields))
        if len(fields) == 0:
            raise FemtocodeError("Record fields ({0}) must contain at least one field-type pair".format(fields))
        for n, t in fields.items():
            if not isinstance(n, string_types) or not isinstance(t, (Schema,) + string_types):
                raise FemtocodeError("all Record fields ({0}: {1}) must map field names (string) to field types (Schema or alias string)".format(n, t))
            if re.match("^" + t_NAME.__doc__ + "$", n) is None:
                raise FemtocodeError("Not a valid field name: {0}".format(json.dumps(n)))

        self.fields = fields
        super(Record, self).__init__(alias)

    def _repr_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return json.dumps(out)

        if self.alias is not None:
            alias = json.dumps(self.alias) + ", "
        else:
            alias = ""

        return "record({0}{1})".format(alias, ", ".join(n + "=" + (t._repr_memo(memo) if isinstance(t, Schema) else repr(t)) for n, t in sorted(self.fields.items())))

    def __contains__(self, other):
        if isinstance(other, Record):
            # other only needs to have fields that self requires; it may have more
            for n, t in self.fields.items():
                if n not in other.fields or other.fields[n] not in t:
                    return False
            return True

        elif isinstance(other, Schema):
            return False

        else:
            for n, t in self.fields.items():
                if not hasattr(other, n) or getattr(other, n) not in t:
                    return False
            return True

    def _field(self, name):
        if isinstance(self.fields[name], Schema) and self.fields[name].alias is not None:
            return self.fields[name].alias
        else:
            return self.fields[name]

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True

        elif isinstance(other, Schema):
            if self.order == other.order:
                return [self._field(n) for n in sorted(self.fields)] < [other._field(n) for n in sorted(other.fields)]
            else:
                return self.order < other.order

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               [self._field(n) for n in sorted(self.fields)] == [other._field(n) for n in sorted(other.fields)]

    def __hash__(self):
        return hash((self.order, tuple(self._field(n) for n in sorted(self.fields))))

    def __call__(self, __alias__=None, **fields):
        return self.__class__(dict(self.fields, **fields), __alias__)

    def _json_memo(self, memo):
        out = self._update_memo(memo)
        if out is not None:
            return {"alias": out}

        out = {"type": "record", "fields": dict((n, t._json_memo(memo)) for n, t in self.fields.items())}
        if self.alias is not None:
            out["alias"] = self.alias

        return out

class Union(Schema):
    order = 7

    def __init__(self, possibilities):
        # Unions can't have aliases because of a case that would lead to unresolvable references
        if not isinstance(possibilities, (list, tuple)):
            raise FemtocodeError("Union possibilities ({0}) must be a list or tuple".format(possibilities))
        for p in possibilities:
            if not isinstance(p, (Schema,) + string_types):
                raise FemtocodeError("all Union possibilities ({0}) must be Schemas or alias strings".format(p))
        if len(possibilities) <= 1:
            raise FemtocodeError("more than one Union possibility required: {0}".format(possibilities))

        # flatten Union of Unions
        ps = []
        aliases = set()
        def merge(p):
            if isinstance(p, Union):
                for pi in p.possibilities:
                    merge(pi)
                aliases.update(p._aliases)
            else:
                ps.append(p)
        
        for p in possibilities:
            merge(p)

        self.possibilities = tuple(sorted(ps))
        super(Union, self).__init__(None)
        self._aliases.update(aliases)

    def _repr_memo(self, memo):
        return "union({0})".format(", ".join(x._repr_memo(memo) if isinstance(x, Schema) else repr(x) for x in self.possibilities))

    def __contains__(self, other):
        if isinstance(other, Union):
            # everything that other can be must also be allowed for self
            for other_t in other.possibilities:
                if not any(other_t in self_t for self_t in self.possibilities):
                    return False
            return True

        elif isinstance(other, Schema):
            # other is a single type, not a Union
            if not any(other in self_t for self_t in self.possibilities):
                return False
            return True

        else:
            # other is an instance (same code, but repeated for clarity)
            if not any(other in self_t for self_t in self.possibilities):
                return False
            return True

    def _possibility(self, index):
        if isinstance(self.possibilities[index], Schema) and self.possibilities[index].alias is not None:
            return self.possibilities[index].alias
        else:
            return self.possibilities[index]

    def __lt__(self, other):
        if isinstance(other, string_types):
            return True

        elif isinstance(other, Schema):
            if self.order == other.order:
                return [self._possibility(i) for i in xrange(len(self.possibilities))] < [other._possibility(i) for i in xrange(len(other.possibilities))]
            else:
                return self.order < other.order

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               [self._possibility(i) for i in xrange(len(self.possibilities))] == [other._possibility(i) for i in xrange(len(other.possibilities))]

    def __hash__(self):
        return hash((self.order, tuple(self._possibility(i) for i in xrange(len(self.possibilities)))))

    def __call__(self, *possibilities):
        return self.__class__(possibilities)

    def _json_memo(self, memo):
        return {"type": "union", "possibilities": [x._json_memo(memo) for x in self.possibilities]}

def _unionNullNumber_helper(schema):
    hasNull = False
    hasNumber = False
    hasAnythingElse = False
    whole = True

    if isinstance(schema, Number):
        hasNumber = True
        whole = schema.whole

    elif isinstance(schema, Union):
        for p in schema.possibilities:
            if isinstance(p, Null):
                hasNull = True
            elif isinstance(p, Number):
                hasNumber = True
                if not p.whole:
                    whole = False
            else:
                hasAnythingElse = True

    return hasNull, hasNumber, hasAnythingElse, whole

def isInt(schema):
    hasNull, hasNumber, hasAnythingElse, whole = _unionNullNumber_helper(schema)
    return not hasNull and hasNumber and not hasAnythingElse and whole

def isFloat(schema):
    hasNull, hasNumber, hasAnythingElse, whole = _unionNullNumber_helper(schema)
    return not hasNull and hasNumber and not hasAnythingElse and not whole

def isNumber(schema):
    hasNull, hasNumber, hasAnythingElse, whole = _unionNullNumber_helper(schema)
    return not hasNull and hasNumber and not hasAnythingElse

def isNullInt(schema):
    hasNull, hasNumber, hasAnythingElse, whole = _unionNullNumber_helper(schema)
    return hasNull and hasNumber and not hasAnythingElse and whole

def isNullFloat(schema):
    hasNull, hasNumber, hasAnythingElse, whole = _unionNullNumber_helper(schema)
    return hasNull and hasNumber and not hasAnythingElse and not whole

def isNullNumber(schema):
    hasNull, hasNumber, hasAnythingElse, whole = _unionNullNumber_helper(schema)
    return hasNull and hasNumber and not hasAnythingElse

def _collectAliases(schema, aliases):
    for n, t in schema._aliases:
        if n in aliases and t != aliases[n]:
            raise FemtocodeError("type alias {0} redefined:\n\n{1}".format(json.dumps(n), compare(t, aliases[n], header=("original", "redefinition"))))
        aliases[n] = t

    if isinstance(schema, Collection):
        if isinstance(schema.items, Schema):
            _collectAliases(schema.items, aliases)

    elif isinstance(schema, Record):
        for x in schema.fields.values():
            if isinstance(x, Schema):
                _collectAliases(x, aliases)

    elif isinstance(schema, Union):
        for x in schema.possibilities:
            if isinstance(x, Schema):
                _collectAliases(x, aliases)

def _getAlias(alias, aliases, top):
    if alias in aliases:
        return aliases[alias]
    else:
        raise FemtocodeError("type alias {0} not defined in any schemas of this Femtocode group:\n\n{1}".format(json.dumps(alias), pretty(top, lambda t: "-->" if t == alias else "   ")))

def _applyAliases(schema, aliases, top):
    if isinstance(schema, Collection):
        if isinstance(schema.items, string_types):
            schema.items = _getAlias(schema.items, aliases, top)
        else:
            schema.items = _applyAliases(schema.items, aliases, top)

    elif isinstance(schema, Record):
        for n, t in schema.fields.items():
            if isinstance(t, string_types):
                schema.fields[n] = _getAlias(t, aliases, top)
            else:
                schema.fields[n] = _applyAliases(t, aliases, top)

    elif isinstance(schema, Union):
        possibilities = []
        for p in schema.possibilities:
            if isinstance(p, string_types):
                possibilities.append(_getAlias(p, aliases, top))
            else:
                possibilities.append(_applyAliases(p, aliases, top))
        # reevaluate whether this ought to be a Union
        schema = union(*possibilities)
        
    return schema

def resolve(schemas):
    aliases = {}
    for schema in schemas:
        if isinstance(schema, Schema):
            _collectAliases(schema, aliases)

    # although it returns a list, it also changes the schemas in-place (only way to make circular references)
    out = []
    for schema in schemas:
        if isinstance(schema, Schema):
            out.append(_applyAliases(schema, aliases, schema))
        else:
            if schema in aliases:
                out.append(aliases[schema])
            else:
                raise FemtocodeError("type alias {0} not defined anywhere in this Femtocode group".format(json.dumps(schema)))

    return out

def _pretty(schema, depth, comma, memo):
    if isinstance(schema, string_types):
        return [(depth, json.dumps(schema) + comma, schema)]

    elif isinstance(schema, (Impossible, Null, Boolean, Number, String)) or isNumber(schema) or isNullNumber(schema):
        return [(depth, schema._repr_memo(memo) + comma, schema)]

    elif isinstance(schema, Collection):
        if schema.alias is not None:
            if schema.alias in memo:
                return [(depth, json.dumps(schema.alias) + comma, schema)]
            else:
                memo.add(schema.alias)

        if schema.most == 0:
            return [(depth, schema._repr_memo(memo) + comma, schema)]

        def generic(schema):
            args = []
            if schema.fewest != 0:
                args.append("fewest={0}".format(schema.fewest))
            if schema.most != almost(inf):
                args.append("most={0}".format(schema.most))
            if schema.most != 0 and schema.ordered:
                args.append("ordered={0}".format(schema.ordered))
            if schema.alias is not None:
                args.append("alias={0}".format(json.dumps(schema.alias)))
            return "collection(", schema.items, ", ".join(args) + ")"

        def specific(schema):
            dimensions = []
            items = schema
            while isinstance(items, Collection) and items.ordered and items.fewest == items.most:
                if not items.ordered:
                    return generic(schema)
                dimensions.append(items.fewest)
                items = items.items

            args = []
            if schema.alias is not None:
                args.append("alias={0}".format(json.dumps(schema.alias)))
            args.extend(map(repr, dimensions))

            if len(dimensions) == 1:
                return "vector(", items, ", ".join(args) + ")"
            elif len(dimensions) == 2:
                return "matrix(", items, ", ".join(args) + ")"
            elif len(dimensions) > 2:
                return "tensor(", items, ", ".join(args) + ")"
            else:
                return generic(schema)

        before, items, after = specific(schema)

        return [(depth, before, schema)] + _pretty(items, depth + 1, "" if after == ")" else ",", memo) + [(depth + 1, after + comma, schema)]

    elif isinstance(schema, Record):
        if schema.alias is not None:
            if schema.alias in memo:
                return [(depth, json.dumps(schema.alias) + comma, schema)]
            else:
                memo.add(schema.alias)

        fields = []
        for i, (n, t) in enumerate(sorted(schema.fields.items())):
            sub = _pretty(t, depth + 1, "," if i < len(schema.fields) - 1 else "", memo)
            fields.extend([(sub[0][0], n + "=" + sub[0][1], sub[0][2])] + sub[1:])

        if schema.alias is not None:
            alias = json.dumps(schema.alias) + ", "
        else:
            alias = ""

        return [(depth, "record(" + alias, schema)] + fields + [(depth + 1, "){0}".format(comma), schema)]

    elif isinstance(schema, Union):
        types = []
        for i, t in enumerate(schema.possibilities):
            sub = _pretty(t, depth + 1, "," if i < len(schema.possibilities) - 1 else "", memo)
            types.extend(sub)

        return [(depth, "union(", schema)] + types + [(depth + 1, "){0}".format(comma), schema)]

    else:
        assert False, "unhandled kind"

def pretty(schema, highlight=lambda t: "", indent="  ", prefix="", memo=None):
    if memo is None:
        memo = set()
    return "\n".join("{0}{1}{2}{3}".format(prefix, highlight(subschema), indent * depth, line) for depth, line, subschema in _pretty(schema, 0, "", memo))

def compare(one, two, header=None, between=lambda t1, t2: " " if t1 == t2 or t1 is None or t2 is None else ">", indent="  ", prefix="", width=None):
    one = _pretty(one, 0, "", set())
    two = _pretty(two, 0, "", set())
    i1 = 0
    i2 = 0
    if width is None:
        width = max(max([len(indent)*depth + len(line) for depth, line, _ in one]), max([len(indent)*depth + len(line) for depth, line, _ in two]))
        if header is not None:
            width = max([width, len(header[0]), len(header[1])])

    if header is not None:
        left, right = header   # assuming header is a 2-tuple of strings
        out = [(prefix + "{0:%d} {1:%d} {2:%d}" % (width, len(between(None, None)), width)).format(left[:width], "|", right[:width]),
               (prefix + "-" * width) + "-+-" + ("-" * width)]
    else:
        out = []

    while i1 < len(one) or i2 < len(two):
        d1, line1, t1 = one[i1] if i1 < len(one) else (d1, "", None)
        d2, line2, t2 = two[i2] if i2 < len(two) else (d2, "", None)

        if d1 >= d2:
            line1 = indent * d1 + line1
            line1 = ("{0:%d}" % width).format(line1[:width])
        if d2 >= d1:
            line2 = indent * d2 + line2
            line2 = ("{0:%d}" % width).format(line2[:width])
        
        if d1 == d2:
            out.append(prefix + line1 + " " + between(t1, t2) + " " + line2)
            i1 += 1
            i2 += 1
        elif d1 > d2:
            out.append(prefix + line1 + " " + between(t1, None) + " " + (" " * width))
            i1 += 1
        elif d2 > d1:
            out.append(prefix + (" " * width) + " " + between(None, t2) + " " + line2)
            i2 += 1

    return "\n".join(out)
    
concrete = ("inf", "null", "boolean", "integer", "real", "extended", "string", "empty")
parameterized = ("almost", "null", "boolean", "integer", "real", "extended", "string", "empty", "collection", "vector", "matrix", "tensor", "record", "union", "intersection", "difference")

impossible = Impossible()
null = Null()
boolean = Boolean()
integer = Number(almost(-inf), almost(inf), True)
real = Number(almost(-inf), almost(inf), False)
extended = Number(-inf, inf, False)
string = String("bytes", 0, almost(inf))
empty = Collection(null, 0, 0, True)

def collection(items, fewest=0, most=almost(inf), ordered=False, alias=None):
    return Collection(items, fewest, most, ordered, alias)

def vector(items, dimension0, alias=None):
    if dimension0 <= 0:
        raise FemtocodeError("vector dimension ({0}) must be positive".format(dimension0))
    return Collection(items, dimension0, dimension0, True, alias)

def matrix(items, dimension0, dimension1, alias=None):
    if dimension0 <= 0 or dimension1 <= 0:
        raise FemtocodeError("matrix dimensions ({0}, {1}) must be positive".format(dimension0, dimension1))
    return Collection(Collection(items, dimension1, dimension1, True), dimension0, dimension0, True, alias)

def tensor(items, *dimensions, **kwds):
    if len(dimensions) > 0 and isinstance(dimensions[-1], string_types):
        alias = dimensions[-1]
        dimensions = dimensions[:-1]
    elif len(kwds) > 0 and "alias" in kwds:
        alias = kwds["alias"]
    else:
        alias = None
    unexpected = set(kwds.keys()).difference(set(["alias"]))
    if len(unexpected) > 0:
        raise FemtocodeError("unexpected keyword arguments in tensor: {0}".format(", ".join(map(repr, kwds.keys()))))
    out = items
    if any(d <= 0 for d in dimensions):
        raise FemtocodeError("tensor dimensions ({0}) must be positive".format(", ".join(map(repr, dimensions))))
    for d in reversed(dimensions):
        out = Collection(out, d, d, True)
    super(Collection, out).__init__(alias)
    return out

def record(__alias__=None, **fields):
    return Record(fields, __alias__)

def union(*types):
    if len(types) == 0:
        raise TypeError("union() takes at least 1 argument (0 given)")

    elif len(types) == 1:
        return types[0]

    elif len(types) > 2:
        # combine them in the order given by the user for more comprehensible error messages
        return union(union(types[0], types[1]), *types[2:])

    else:
        one, two = types

        if isinstance(one, string_types) or isinstance(two, string_types):
            if one == two:
                return one
            else:
                return Union([one, two])

        elif isinstance(one, Union) and isinstance(two, Union):
            out = union(*(one.possibilities + two.possibilities))

        elif isinstance(one, Union):
            possibilities = []
            filled = False
            for p in one.possibilities:
                combined = union(p, two)
                if not isinstance(combined, Union):
                    possibilities.append(combined)
                    filled = True
                else:
                    possibilities.append(p)

            if not filled:
                possibilities.append(two)
            out = Union(possibilities)

        elif isinstance(two, Union):
            possibilities = []
            filled = False
            for p in two.possibilities:
                combined = union(p, one)
                if not isinstance(combined, Union):
                    possibilities.append(combined)
                    filled = True
                else:
                    possibilities.append(p)

            if not filled:
                possibilities.append(one)
            out = Union(possibilities)

        elif isinstance(one, Impossible) and isinstance(two, Impossible):
            out = impossible(one.reason if two.reason is None else two.reason)

        elif isinstance(one, Impossible):
            # in a language that permits runtime errors, union(impossible, X) == X
            # but in Femtocode, union(impossible, X) == impossible
            out = one()

        elif isinstance(two, Impossible):
            # in a language that permits runtime errors, union(impossible, X) == X
            # but in Femtocode, union(impossible, X) == impossible
            out = two()

        elif one.order != two.order:
            # there is no overlap among different kinds
            out = Union([one, two])
        
        elif isinstance(one, Null) and isinstance(two, Null):
            out = null()

        elif isinstance(one, Boolean) and isinstance(two, Boolean):
            if one.just is True:
                oneposs = set([True])
            elif one.just is False:
                oneposs = set([False])
            else:
                oneposs = set([True, False])

            if two.just is True:
                twoposs = set([True])
            elif two.just is False:
                twoposs = set([False])
            else:
                twoposs = set([True, False])

            possibilities = oneposs.union(twoposs)
            if possibilities == set([True]):
                out = boolean(True)
            elif possibilities == set([False]):
                out = boolean(False)
            else:
                out = boolean()

        elif isinstance(one, Number) and isinstance(two, Number):
            if one in two:
                # two is the superset, it contains one
                out = two()

            elif two in one:
                # one is the superset, it contains two
                out = one()

            elif one.whole and two.whole:
                # both integer: they can be glued if there's 1 unit gap or less
                low, high = sorted([one, two])
                if low.max >= high.min - 1:
                    out = Number(almost.min(low.min, high.min), almost.max(low.max, high.max), True)
                else:
                    out = Union([one, two])

            elif one.whole or two.whole:
                # one integer, other not and neither is contained: they can be glued if they extend the interval from open to closed
                if one.whole:
                    inty, realy = one, two
                else:
                    inty, realy = two, one

                if inty in Number(realy.min.real, realy.max.real, False):
                    out = Number(almost.min(one.min, two.min), almost.max(one.max, two.max), False)
                else:
                    out = Union([difference(inty, realy), realy])

            else:
                # neither integer: they can be glued if there's no gap
                low, high = sorted([one, two])
                if low.max.real == high.min.real:
                    if isinstance(low.max, almost) and isinstance(high.min, almost):
                        # they just touch and they're both open intervals; can't glue
                        out = Union([one, two])
                    else:
                        out = Number(almost.min(low.min, high.min), almost.max(low.max, high.max), False)
                elif low.max >= high.min:
                    out = Number(almost.min(low.min, high.min), almost.max(low.max, high.max), False)
                else:
                    out = Union([one, two])

        elif isinstance(one, String) and isinstance(two, String):
            if one.charset == two.charset:
                number = union(Number(one.fewest, one.most, True), Number(two.fewest, two.most, True))
                if isinstance(number, Number) and number.whole:
                    out = String(one.charset, number.min, number.max)
                elif isinstance(number, Union) and all(isinstance(p, Number) and p.whole for p in number.possibilities):
                    out = Union([String(one.charset, p.min, p.max) for p in number.possibilities])
                else:
                    assert False, "union(Number, Number) is {0}".format(number)
            else:
                out = Union([one, two])

        elif isinstance(one, Collection) and isinstance(two, Collection):
            if one.most == 0 or two.most == 0 or one.items == two.items:
                if one.most == 0:
                    items = two.items
                    ordered = two.ordered
                elif two.most == 0:
                    items = one.items
                    ordered = one.ordered
                else:
                    items = one.items
                    ordered = one.ordered and two.ordered

                number = union(Number(one.fewest, one.most, True), Number(two.fewest, two.most, True))

                if isinstance(number, Number) and number.whole:
                    out = Collection(items, number.min, number.max, ordered)
                elif isinstance(number, Union) and all(isinstance(p, Number) and p.whole for p in number.possibilities):
                    out = Union([Collection(items, p.min, p.max, ordered) for p in number.possibilities])
                else:
                    assert False, "union(Number, Number) is {0}".format(number)
                
            else:
                out = Union([one, two])

        elif isinstance(one, Record) and isinstance(two, Record):
            if set(one.fields) == set(two.fields):
                if all(one.fields[n] in two.fields[n] for n in one.fields):
                    out = two()
                elif all(two.fields[n] in one.fields[n] for n in one.fields):
                    out = one()
                else:
                    out = Union([one, two])
            else:
                out = Union([one, two])

        else:
            assert False, "unhandled case"
            
        # don't lose any aliases because one and two have been replaced by their union
        out._aliases.update(one._aliases)
        out._aliases.update(two._aliases)
        return out
        
def intersection(*types):
    if len(types) == 0:
        raise TypeError("intersection() takes at least 1 argument (0 given)")

    elif len(types) == 1:
        return types[0]

    elif len(types) > 2:
        # combine them in the order given by the user for more comprehensible error messages
        return intersection(intersection(types[0], types[1]), *types[2:])

    else:
        one, two = types
            
        if isinstance(one, Union) and not isinstance(two, Union):
            possibilities = []
            reason = None
            for p in one.possibilities:
                result = intersection(p, two)
                if not isinstance(result, Impossible):
                    possibilities.append(result)
                elif reason is None:
                    reason = result.reason
            
            if len(possibilities) == 0:
                out = impossible(reason)
            elif len(possibilities) == 1:
                out = possibilities[0]
            else:
                out = union(*possibilities)

        elif isinstance(two, Union):
            # includes the case when one and two are both Unions
            possibilities = []
            reason = None
            for p in two.possibilities:
                result = intersection(one, p)
                if not isinstance(result, Impossible):
                    possibilities.append(result)
                elif reason is None:
                    reason = result.reason
            
            if len(possibilities) == 0:
                out = impossible(reason)
            elif len(possibilities) == 1:
                out = possibilities[0]
            else:
                out = union(*possibilities)

        elif isinstance(one, Impossible) and isinstance(two, Impossible):
            out = impossible(one.reason if two.reason is None else two.reason)

        elif isinstance(one, Impossible):
            out = one()

        elif isinstance(two, Impossible):
            out = two()

        elif one.order != two.order:
            # there is no overlap among different kinds
            out = impossible("{0} and {1} have no overlap.".format(one.name(True), two.name(True)))

        elif isinstance(one, Null) and isinstance(two, Null):
            out = null()

        elif isinstance(one, Boolean) and isinstance(two, Boolean):
            if one.just is True:
                oneposs = set([True])
            elif one.just is False:
                oneposs = set([False])
            else:
                oneposs = set([True, False])

            if two.just is True:
                twoposs = set([True])
            elif two.just is False:
                twoposs = set([False])
            else:
                twoposs = set([True, False])

            possibilities = oneposs.intersection(twoposs)
            if possibilities == set([True]):
                out = boolean(True)
            elif possibilities == set([False]):
                out = boolean(False)
            else:
                out = boolean()

        elif isinstance(one, Number) and isinstance(two, Number):
            if one in two:
                # one is the subset, contained within two
                out = one()

            elif two in one:
                # two is the subset, contained within one
                out = two()

            else:
                low, high = sorted([one, two])

                if low.max.real == high.min.real:
                    if not isinstance(low.max, almost) and not isinstance(high.min, almost):
                        out = Number(low.max.real, low.max.real, round(low.max.real) == low.max.real)
                    else:
                        out = impossible("{0} and {1} are both open at {2}.".format(low, high, low.max.real))

                elif low.max < high.min:
                    out = impossible("{0} is entirely below {1}.".format(low, high))

                else:
                    try:
                        out = Number(almost.complement(almost.max(almost.complement(low.min), almost.complement(high.min))),
                                     almost.complement(almost.min(almost.complement(low.max), almost.complement(high.max))),
                                     low.whole or high.whole)
                    except FemtocodeError:
                        out = impossible()   # ???

        elif isinstance(one, String) and isinstance(two, String):
            if one.charset == two.charset:
                number = intersection(Number(one.fewest, one.most, True), Number(two.fewest, two.most, True))
                if isinstance(number, Number) and number.whole:
                    out = String(one.charset, number.min, number.max)
                elif isinstance(number, Impossible):
                    out = impossible("Size intervals of {0} and {1} do not overlap.".format(one, two))
                else:
                    assert False, "intersection(Number, Number) is {0}".format(number)
            else:
                out = impossible("Charsets {0} and {1} do not overlap.".format(one, two))

        elif isinstance(one, Collection) and isinstance(two, Collection):
            if one.most == 0 and two.most == 0:
                items = null
                ordered = True
            elif one.most == 0:
                items = two.items
                ordered = two.ordered
            elif two.most == 0:
                items = one.items
                ordered = one.ordered
            else:
                items = intersection(one.items, two.items)
                ordered = one.ordered and two.ordered

            if not isinstance(items, Impossible):
                number = intersection(Number(one.fewest, one.most, True), Number(two.fewest, two.most, True))
                if isinstance(number, Number) and number.whole:
                    out = Collection(items, number.min, number.max, ordered)
                elif isinstance(number, Impossible):
                    out = impossible("Size intervals of collections do not overlap in\n{0}".format(compare(one, two)))
                else:
                    assert False, "intersection(Number, Number) is {0}".format(number)
            else:
                out = impossible("Item schemas of collections do not overlap in\n{0}".format(compare(one, two)))

        elif isinstance(one, Record) and isinstance(two, Record):
            if set(one.fields) == set(two.fields):
                fields = {}
                out = None
                for n in one.fields:
                    fields[n] = intersection(one.fields[n], two.fields[n])
                    if isinstance(fields[n], Impossible):
                        out = impossible("Field {0} has no overlap in\n{1}".format(json.dumps(n), compare(one, two)))
                        break
                if out is None:
                    out = Record(fields)
            else:
                out = impossible("Field sets differ in\n{0}".format(compare(one, two)))

        else:
            assert False, "unhandled case"
            
        # don't lose any aliases because one and two have been replaced by their union
        out._aliases.update(one._aliases)
        out._aliases.update(two._aliases)
        return out

def difference(universal, excluded):
    if isinstance(universal, Union):
        out = union(*(difference(p, excluded) for p in universal.possibilities))

    elif isinstance(excluded, Union):
        out = universal()
        for p in excluded.possibilities:
            out = difference(out, p)

    elif isinstance(universal, Impossible) and isinstance(excluded, Impossible):
        out = impossible(universal.reason if excluded.reason is None else excluded.reason)

    elif isinstance(universal, Impossible):
        out = universal()

    elif isinstance(excluded, Impossible):
        out = excluded()

    elif universal.order != excluded.order:
        out = universal()

    elif isinstance(universal, Null) and isinstance(excluded, Null):
        out = impossible("null type is completely covered by null type.")

    elif isinstance(universal, Boolean) and isinstance(excluded, Boolean):
        if universal.just is True:
            universalposs = set([True])
        elif universal.just is False:
            universalposs = set([False])
        else:
            universalposs = set([True, False])

        if excluded.just is True:
            excludedposs = set([True])
        elif excluded.just is False:
            excludedposs = set([False])
        else:
            excludedposs = set([True, False])

        possibilities = universalposs.difference(excludedposs)
        if possibilities == set([True]):
            out = boolean(True)
        elif possibilities == set([False]):
            out = boolean(False)
        else:
            out = impossible("Removing {True, False} from the set {True, False} yields no possibilities.")

    elif isinstance(universal, Number) and isinstance(excluded, Number):
        if not universal.whole and excluded.whole and excluded.min != excluded.max:
            # do not attempt to remove (potentially very many) integers from a continuous interval;
            # returning too-inclusive a result is okay
            out = universal()
        else:
            if almost.min(universal.min, excluded.min) == excluded.min:
                # excluded starts below universal
                if almost.max(universal.max, excluded.max) == excluded.max:
                    out = impossible("{0} completely covers {1}.".format(excluded, universal))
                elif excluded.max.real < universal.min.real or (excluded.max.real == universal.min.real and (isinstance(excluded.max, almost) or isinstance(universal.min, almost))):
                    out = universal()
                else:
                    out = Number(almost.complement(excluded.max), universal.max, universal.whole)

            elif almost.max(universal.max, excluded.max) == excluded.max:
                # excluded ends above universal
                if almost.min(universal.min, excluded.min) == excluded.min:
                    out = impossible("{0} completely covers {1}.".format(excluded, universal))
                elif excluded.min.real > universal.max.real or (excluded.min.real == universal.max.real and (isinstance(excluded.min, almost) or isinstance(universal.max, almost))):
                    out = universal()
                else:
                    out = Number(universal.min, almost.complement(excluded.min), universal.whole)

            else:
                # excluded is in the middle of universal
                out = Union([Number(universal.min, almost.complement(excluded.min), universal.whole),
                             Number(almost.complement(excluded.max), universal.max, universal.whole)])

    elif isinstance(universal, String) and isinstance(excluded, String):
        if universal.charset == excluded.charset:
            number = difference(Number(universal.fewest, universal.most, True), Number(excluded.fewest, excluded.most, True))
            if isinstance(number, Number):
                out = String(universal.charset, number.min, number.max)
            elif isinstance(number, Union) and all(isinstance(p, Number) and p.whole for p in number.possibilities) and len(number.possibilities) == 2:
                one = number.possibilities[0]
                two = number.possibilities[1]
                out = Union([String(universal.charset, one.min, one.max), String(universal.charset, two.min, two.max)])
            elif isinstance(number, Impossible):
                out = impossible("Size range of {0} completely covers {1}.".format(excluded, universal))
            else:
                assert False, "difference(Number, Number) is {0}".format(number)
        else:
            out = universal()

    elif isinstance(universal, Collection) and isinstance(excluded, Collection):
        if universal.most == 0:
            if excluded.most == 0:
                out = impossible("Type of empty collections is completely covered by empty collections.")
            else:
                out = universal()

        elif excluded.most == 0:
            number = difference(Number(universal.fewest, universal.most, True), Number(0, 0, True))
            out = Collection(universal.items, number.min, number.max, universal.ordered)

        else:
            possibilities = []

            items1 = difference(universal.items, excluded.items)
            if not isinstance(items1, Impossible):
                possibilities.append(Collection(items1, universal.fewest, universal.most, universal.ordered))

            items2 = intersection(universal.items, excluded.items)
            if not isinstance(items2, Impossible):
                number = difference(Number(universal.fewest, universal.most, True), Number(excluded.fewest, excluded.most, True))

                if isinstance(number, Number):
                    possibilities.append(Collection(items2, number.min, number.max, universal.ordered))
                elif isinstance(number, Union) and all(isinstance(p, Number) and p.whole for p in number.possibilities) and len(number.possibilities) == 2:
                    one = number.possibilities[0]
                    two = number.possibilities[1]
                    possibilities.append(Collection(items2, one.min, one.max, universal.ordered))
                    possibilities.append(Collection(items2, two.min, two.max, universal.ordered))
                elif isinstance(number, Impossible):
                    pass
                else:
                    assert False, "difference(Number, Number) is {0}".format(number)

            if len(possibilities) == 0:
                out = impossible("Size and contents completely covered in\n{0}".format(compare(universal, excluded, ("universal set", "exclusion region"))))
            elif len(possibilities) == 1:
                out = possibilities[0]
            else:
                out = Union(possibilities)

    elif isinstance(universal, Record) and isinstance(excluded, Record):
        if set(universal.fields) == set(excluded.fields):
            fields = universal.fields
            possibilities = []
            for n in sorted(universal.fields):
                fields = dict(fields)
                fields[n] = difference(universal.fields[n], excluded.fields[n])
                if not any(isinstance(t, Impossible) for t in fields.values()):
                    possibilities.append(Record(dict(fields)))
                fields[n] = intersection(universal.fields[n], excluded.fields[n])

            if len(possibilities) == 0:
                out = impossible("Size and contents completely covered in\n{0}".format(compare(universal, excluded, ("universal set", "exclusion region"))))
            elif len(possibilities) == 1:
                out = possibilities[0]
            else:
                out = Union(possibilities)

        else:
            out = universal()

    else:
        assert False, "unhandled case"

    # don't lose any aliases because universal and excluded have been replaced by their union
    out._aliases.update(universal._aliases)
    out._aliases.update(excluded._aliases)
    return out

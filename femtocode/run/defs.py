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

import re
import json

from femtocode.parser import t_NAME
from femtocode.defs import ProgrammingError, FemtocodeError
from femtocode.py23 import *
from femtocode.asts.statementlist import *

class Dataset(object):
    @staticmethod
    def checknames(names):
        for name in names:
            if re.match("^" + t_NAME.__doc__ + "$", name) is None:
                raise FemtocodeError("Not a valid field name: {0}".format(json.dumps(name)))

    def __init__(self, schemas, columns):
        self.schemas = schemas
        self.columns = columns
        self.entries = 0

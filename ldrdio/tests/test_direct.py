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

import time
import unittest

import numpy

from client.StripedClient import StripedClient

class TestDirect(unittest.TestCase):
    def runTest(self):
        pass

    def test_printout(self):
        client = StripedClient("http://dbdata0vm.fnal.gov:9091/striped/app")

        print(client.dataset("ZZ_13TeV_pythia8").schema)
        print(client.dataset("ZZ_13TeV_pythia8").rginfo([98]))
        print(client.dataset("ZZ_13TeV_pythia8").column("Muon.pt").stripe(0))
        print(client.dataset("ZZ_13TeV_pythia8").column("Muon.pt").sizeColumn.Name)

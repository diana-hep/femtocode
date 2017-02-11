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

from femtocode.fromroot._fastreader import fillarrays

class TestFastReader(unittest.TestCase):
    def runTest(self):
        pass

    def test_fastReader(self):
        data = numpy.ones(120463, dtype=numpy.float64) * 1.1
        size = numpy.ones(48131, dtype=numpy.uint64) * 999

        startTime = time.time()
        fillarrays("file:/home/pivarski/storage/data/00000000-0000-0000-0000-000000000000.root", "Events", [("patElectrons_slimmedElectrons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patElectrons_slimmedElectrons__PAT.obj", data, size)])
        endTime = time.time()

        print("data {}".format(data))
        print("size {}".format(size))
        print("time {}".format(endTime - startTime))


# "root://cmseos.fnal.gov//store/user/pivarski/femtocodetest/RunIISpring16MiniAODv2_SMS-T1tttt_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_MINIAODSIM_PUSpring16Fast_80X_mcRun2_asymptotic_2016_miniAODv2_v0-v1/00000000-0000-0000-0000-000000000000.root"

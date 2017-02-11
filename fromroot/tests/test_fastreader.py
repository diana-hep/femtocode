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
    fileName = "file:/home/pivarski/storage/data/00000000-0000-0000-0000-000000000000.root"
    # fileName = "root://cmseos.fnal.gov//store/user/pivarski/femtocodetest/RunIISpring16MiniAODv2_SMS-T1tttt_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_MINIAODSIM_PUSpring16Fast_80X_mcRun2_asymptotic_2016_miniAODv2_v0-v1/00000000-0000-0000-0000-000000000000.root"

    treeName = "Events"

    numEvents = 48131
    numTaus = 305544
    numJets = 806177
    numMuons = 132274
    numPhotons = 139746
    numElectrons = 120463
    numAK8Jets = 87530

    def runTest(self):
        pass

    def test_flat(self):
        data = numpy.zeros(self.numEvents, dtype=numpy.float64)

        fillarrays(self.fileName, self.treeName, [("recoBeamSpot_offlineBeamSpot__HLT.obj.position_.fCoordinates.fZ", data)])
        print("data {}".format(data))

    def test_structured(self):
        data = numpy.zeros(self.numElectrons, dtype=numpy.float64)
        size = numpy.zeros(self.numEvents, dtype=numpy.uint64)

        fillarrays(self.fileName, self.treeName, [("patElectrons_slimmedElectrons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patElectrons_slimmedElectrons__PAT.obj", data, size)])

        print("data {}".format(data))
        print("size {}".format(size))

    def test_many(self):
        toget = []

        beam_x = numpy.empty(self.numEvents, dtype=numpy.float64)
        beam_y = numpy.empty(self.numEvents, dtype=numpy.float64)
        beam_z = numpy.empty(self.numEvents, dtype=numpy.float64)
        toget.append(("recoBeamSpot_offlineBeamSpot__HLT.obj.position_.fCoordinates.fX", beam_x))
        toget.append(("recoBeamSpot_offlineBeamSpot__HLT.obj.position_.fCoordinates.fY", beam_y))
        toget.append(("recoBeamSpot_offlineBeamSpot__HLT.obj.position_.fCoordinates.fZ", beam_z))

        electron_size = numpy.ones(self.numEvents, dtype=numpy.uint64)
        electron_pt = numpy.ones(self.numElectrons, dtype=numpy.float64)
        electron_eta = numpy.ones(self.numElectrons, dtype=numpy.float64)
        electron_phi = numpy.ones(self.numElectrons, dtype=numpy.float64)
        toget.append(("patElectrons_slimmedElectrons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patElectrons_slimmedElectrons__PAT.obj", electron_pt, electron_size))
        toget.append(("patElectrons_slimmedElectrons__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "patElectrons_slimmedElectrons__PAT.obj", electron_eta, electron_size))
        toget.append(("patElectrons_slimmedElectrons__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "patElectrons_slimmedElectrons__PAT.obj", electron_phi, electron_size))

        fillarrays(self.fileName, self.treeName, toget)

        print("beam_x {}".format(beam_x))
        print("beam_y {}".format(beam_y))
        print("beam_z {}".format(beam_z))

        print("electron_size {}".format(electron_size))
        print("electron_pt {}".format(electron_pt))
        print("electron_eta {}".format(electron_eta))
        print("electron_phi {}".format(electron_phi))


# patJets_slimmedJetsAK8__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
# patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
# patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
# patPhotons_slimmedPhotons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
# patTaus_slimmedTaus__PAT.obj.m_state.p4Polar_.fCoordinates.fPt

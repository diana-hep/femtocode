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
    fileName = "/home/pivarski/storage/data/00000000-0000-0000-0000-000000000000.root"
    # fileName = "root://cmseos.fnal.gov//store/user/pivarski/femtocodetest/RunIISpring16MiniAODv2_SMS-T1tttt_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_MINIAODSIM_PUSpring16Fast_80X_mcRun2_asymptotic_2016_miniAODv2_v0-v1/00000000-0000-0000-0000-000000000000.root"

    treeName = "Events"

    numEvents = 48131
    numTaus = 305544
    numJets = 806177
    numMuons = 132274
    numPhotons = 139746
    numElectrons = 120463
    numJetAK8s = 87530

    def runTest(self):
        pass

    def test_flat(self):
        data = numpy.zeros(self.numEvents, dtype=numpy.float64)

        fillarrays(self.fileName, self.treeName, [("recoBeamSpot_offlineBeamSpot__HLT.obj.position_.fCoordinates.fZ", data)])
        print("data ({} MB) {}".format(len(data) * 8.0 / 1024**2, data))

    def test_structured(self):
        data = numpy.zeros(self.numElectrons, dtype=numpy.float64)
        size = numpy.zeros(self.numEvents, dtype=numpy.uint64)

        fillarrays(self.fileName, self.treeName, [("patElectrons_slimmedElectrons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patElectrons_slimmedElectrons__PAT.obj", data, size)])

        print("data ({} MB) {}".format(len(data) * 8.0 / 1024**2, data))
        print("size ({} MB) {}".format(len(size) * 8.0 / 1024**2, size))

    def test_structured2(self):
        data = numpy.zeros(self.numJets, dtype=numpy.float64)
        size = numpy.zeros(self.numEvents, dtype=numpy.uint64)

        startTime = time.time()
        fillarrays(self.fileName, self.treeName, [("patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patJets_slimmedJets__PAT.obj", data, size)])
        endTime = time.time()

        print("data ({} MB) {}".format(len(data) * 8.0 / 1024**2, data))
        print("size ({} MB) {}".format(len(size) * 8.0 / 1024**2, size))
        mb = (len(data) + len(size)) * 8.0 / 1024**2
        sec = endTime - startTime
        print("{} MB in {} sec at {} MB/sec".format(mb, sec, mb/sec))

    def test_subdir(self):
        # "root://cmseos.fnal.gov//store/user/pivarski/TrackResonanceNtuple.root"

        mass_mumu = numpy.zeros(751919, dtype=numpy.float32)
        startTime = time.time()
        fillarrays("/home/pivarski/storage/data/TrackResonanceNtuple.root", "TrackResonanceNtuple/twoMuon", [("mass_mumu", mass_mumu)])
        endTime = time.time()
        mb = len(mass_mumu) * 4.0 / 1024**2
        sec = endTime - startTime
        print("mass_mumu ({} MB in {} sec at {} MB/sec) {}".format(mb, sec, mb/sec, mass_mumu))

        mass_piP = numpy.zeros(1989730, dtype=numpy.float32)
        mass_KK = numpy.zeros(1989730, dtype=numpy.float32)
        mass_pipi = numpy.zeros(1989730, dtype=numpy.float32)
        startTime = time.time()
        fillarrays("/home/pivarski/storage/data/TrackResonanceNtuple.root", "TrackResonanceNtuple/twoTrack", [("mass_piP", mass_piP), ("mass_KK", mass_KK), ("mass_pipi", mass_pipi)])
        endTime = time.time()
        mb = (len(mass_piP) + len(mass_KK) + len(mass_pipi)) * 4.0 / 1024**2
        sec = endTime - startTime
        print("mass_piP ({} MB in {} sec at {} MB/sec) {}".format(mb, sec, mb/sec, mass_piP))

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

        muon_size = numpy.ones(self.numEvents, dtype=numpy.uint64)
        muon_pt = numpy.ones(self.numMuons, dtype=numpy.float64)
        muon_eta = numpy.ones(self.numMuons, dtype=numpy.float64)
        muon_phi = numpy.ones(self.numMuons, dtype=numpy.float64)
        toget.append(("patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patMuons_slimmedMuons__PAT.obj", muon_pt, muon_size))
        toget.append(("patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "patMuons_slimmedMuons__PAT.obj", muon_eta, muon_size))
        toget.append(("patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "patMuons_slimmedMuons__PAT.obj", muon_phi, muon_size))

        tau_size = numpy.ones(self.numEvents, dtype=numpy.uint64)
        tau_pt = numpy.ones(self.numTaus, dtype=numpy.float64)
        tau_eta = numpy.ones(self.numTaus, dtype=numpy.float64)
        tau_phi = numpy.ones(self.numTaus, dtype=numpy.float64)
        toget.append(("patTaus_slimmedTaus__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patTaus_slimmedTaus__PAT.obj", tau_pt, tau_size))
        toget.append(("patTaus_slimmedTaus__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "patTaus_slimmedTaus__PAT.obj", tau_eta, tau_size))
        toget.append(("patTaus_slimmedTaus__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "patTaus_slimmedTaus__PAT.obj", tau_phi, tau_size))

        photon_size = numpy.ones(self.numEvents, dtype=numpy.uint64)
        photon_pt = numpy.ones(self.numPhotons, dtype=numpy.float64)
        photon_eta = numpy.ones(self.numPhotons, dtype=numpy.float64)
        photon_phi = numpy.ones(self.numPhotons, dtype=numpy.float64)
        toget.append(("patPhotons_slimmedPhotons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patPhotons_slimmedPhotons__PAT.obj", photon_pt, photon_size))
        toget.append(("patPhotons_slimmedPhotons__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "patPhotons_slimmedPhotons__PAT.obj", photon_eta, photon_size))
        toget.append(("patPhotons_slimmedPhotons__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "patPhotons_slimmedPhotons__PAT.obj", photon_phi, photon_size))

        jet_size = numpy.ones(self.numEvents, dtype=numpy.uint64)
        jet_pt = numpy.ones(self.numJets, dtype=numpy.float64)
        jet_eta = numpy.ones(self.numJets, dtype=numpy.float64)
        jet_phi = numpy.ones(self.numJets, dtype=numpy.float64)
        toget.append(("patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patJets_slimmedJets__PAT.obj", jet_pt, jet_size))
        toget.append(("patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "patJets_slimmedJets__PAT.obj", jet_eta, jet_size))
        toget.append(("patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "patJets_slimmedJets__PAT.obj", jet_phi, jet_size))

        jetAK8_size = numpy.ones(self.numEvents, dtype=numpy.uint64)
        jetAK8_pt = numpy.ones(self.numJetAK8s, dtype=numpy.float64)
        jetAK8_eta = numpy.ones(self.numJetAK8s, dtype=numpy.float64)
        jetAK8_phi = numpy.ones(self.numJetAK8s, dtype=numpy.float64)
        toget.append(("patJets_slimmedJetsAK8__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "patJets_slimmedJetsAK8__PAT.obj", jetAK8_pt, jetAK8_size))
        toget.append(("patJets_slimmedJetsAK8__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "patJets_slimmedJetsAK8__PAT.obj", jetAK8_eta, jetAK8_size))
        toget.append(("patJets_slimmedJetsAK8__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "patJets_slimmedJetsAK8__PAT.obj", jetAK8_phi, jetAK8_size))

        startTime = time.time()
        fillarrays(self.fileName, self.treeName, toget)
        endTime = time.time()

        print("beam_x {}".format(beam_x))
        print("beam_y {}".format(beam_y))
        print("beam_z {}".format(beam_z))

        print("electron_size {}".format(electron_size))
        print("electron_pt {}".format(electron_pt))
        print("electron_eta {}".format(electron_eta))
        print("electron_phi {}".format(electron_phi))

        print("muon_size {}".format(muon_size))
        print("muon_pt {}".format(muon_pt))
        print("muon_eta {}".format(muon_eta))
        print("muon_phi {}".format(muon_phi))

        print("tau_size {}".format(tau_size))
        print("tau_pt {}".format(tau_pt))
        print("tau_eta {}".format(tau_eta))
        print("tau_phi {}".format(tau_phi))

        print("photon_size {}".format(photon_size))
        print("photon_pt {}".format(photon_pt))
        print("photon_eta {}".format(photon_eta))
        print("photon_phi {}".format(photon_phi))

        print("jet_size {}".format(jet_size))
        print("jet_pt {}".format(jet_pt))
        print("jet_eta {}".format(jet_eta))
        print("jet_phi {}".format(jet_phi))

        print("jetAK8_size {}".format(jetAK8_size))
        print("jetAK8_pt {}".format(jetAK8_pt))
        print("jetAK8_eta {}".format(jetAK8_eta))
        print("jetAK8_phi {}".format(jetAK8_phi))

        totalMB = sum([len(beam_x), len(beam_y), len(beam_z), len(electron_size), len(electron_pt), len(electron_eta), len(electron_phi), len(muon_size), len(muon_pt), len(muon_eta), len(muon_phi), len(tau_size), len(tau_pt), len(tau_eta), len(tau_phi), len(photon_size), len(photon_pt), len(photon_eta), len(photon_phi), len(jet_size), len(jet_pt), len(jet_eta), len(jet_phi), len(jetAK8_size), len(jetAK8_pt), len(jetAK8_eta), len(jetAK8_phi)]) * 8.0 / 1024**2

        print("{} MB in {} sec at {} MB/sec".format(totalMB, endTime - startTime, totalMB / (endTime - startTime)))

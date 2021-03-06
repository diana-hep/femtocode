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

from femtocode.rootio.dataset import ROOTDataset

class TestDeclare(unittest.TestCase):
    def runTest(self):
        pass

    def test_real(self):
        declaration = """
define:
  MuOnia-2016-CF-23Sep2016-v1:
    format: root
    groupsize: 10   # 10 files per group
    paths:
      - root://cmseos.fnal.gov//store/data/Run2016[CF]/MuOnia/AOD/23Sep2016-v1/*/*.root

  MuOnia-2016-CF-PromptReco-v2:
    format: root
    paths:
      - root://cmseos.fnal.gov//store/data/Run2016C/MuOnia/AOD/PromptReco-v2/*/*.root
      - root://cmseos.fnal.gov//store/data/Run2016F/MuOnia/AOD/PromptReco-v2/

  local:
    format: root
    paths:
      - /home/pivarski/storage/data/00000000-0000-0000-0000-000000000000.root

name: MuOnia

sources:
  - local

schema:

  muons:
    type: collection
    items:
      type: record
      fields:
        pt:
          type: real
          min: 0
          max: almost(inf)
          from:
            tree: Events
            branch: patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
            dtype: float64
        eta:
          type: real
          from:
            tree: Events
            branch: patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fEta
            dtype: float64
        phi:
          type: real
          min: -pi
          max: pi
          from:
            tree: Events
            branch: patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi
            dtype: float64

  jets:
    type: collection
    items:
      type: record
      fields:
        pt:
          type: real
          min: 0
          max: almost(inf)
          from:
            tree: Events
            branch: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
            dtype: float64
        eta:
          type: real
          from:
            tree: Events
            branch: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fEta
            dtype: float64
        phi:
          type: real
          min: -pi
          max: pi
          from:
            tree: Events
            branch: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi
            dtype: float64
        mass:
          type: real
          min: 0
          max: almost(inf)
          from:
            tree: Events
            branch: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fM
            dtype: float64
"""

        dataset = ROOTDataset.fromYamlString(declaration)

        asjson = dataset.toJson()

        self.assertEqual(asjson, {"name": "MuOnia", "numGroups": 1, "numEntries": 48131, "groups": [{"files": ["/home/pivarski/storage/data/00000000-0000-0000-0000-000000000000.root"], "segments": {"jets[]-mass": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 806177}, "jets[]-pt": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 806177}, "muons[]-pt": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 132274}, "muons[]-eta": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 132274}, "jets[]-eta": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 806177}, "jets[]-phi": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 806177}, "muons[]-phi": {"files": None, "sizeLength": 48131, "numEntries": 48131, "dataLength": 132274}}, "numEntries": 48131, "id": 0}], "class": "femtocode.rootio.dataset.ROOTDataset", "columns": {"jets[]-mass": {"dataBranch": "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fM", "dataType": "float64", "tree": "Events", "sizeBranch": "patJets_slimmedJets__PAT.obj", "data": "jets[]-mass", "size": "jets[]@size"}, "jets[]-pt": {"dataBranch": "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "dataType": "float64", "tree": "Events", "sizeBranch": "patJets_slimmedJets__PAT.obj", "data": "jets[]-pt", "size": "jets[]@size"}, "muons[]-pt": {"dataBranch": "patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt", "dataType": "float64", "tree": "Events", "sizeBranch": "patMuons_slimmedMuons__PAT.obj", "data": "muons[]-pt", "size": "muons[]@size"}, "muons[]-eta": {"dataBranch": "patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "dataType": "float64", "tree": "Events", "sizeBranch": "patMuons_slimmedMuons__PAT.obj", "data": "muons[]-eta", "size": "muons[]@size"}, "jets[]-eta": {"dataBranch": "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fEta", "dataType": "float64", "tree": "Events", "sizeBranch": "patJets_slimmedJets__PAT.obj", "data": "jets[]-eta", "size": "jets[]@size"}, "jets[]-phi": {"dataBranch": "patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "dataType": "float64", "tree": "Events", "sizeBranch": "patJets_slimmedJets__PAT.obj", "data": "jets[]-phi", "size": "jets[]@size"}, "muons[]-phi": {"dataBranch": "patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi", "dataType": "float64", "tree": "Events", "sizeBranch": "patMuons_slimmedMuons__PAT.obj", "data": "muons[]-phi", "size": "muons[]@size"}}, "schema": {"jets": {"items": {"fields": {"phi": {"max": 3.141592653589793, "type": "real", "min": -3.141592653589793}, "eta": "real", "mass": {"max": {"almost": "inf"}, "type": "real", "min": 0}, "pt": {"max": {"almost": "inf"}, "type": "real", "min": 0}}, "type": "record"}, "type": "collection"}, "muons": {"items": {"fields": {"phi": {"max": 3.141592653589793, "type": "real", "min": -3.141592653589793}, "eta": "real", "pt": {"max": {"almost": "inf"}, "type": "real", "min": 0}}, "type": "record"}, "type": "collection"}}})

        self.assertEqual(ROOTDataset.fromJson(asjson), dataset)

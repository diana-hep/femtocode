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

import femtocode.fromroot.declare as declare

class TestDeclare(unittest.TestCase):
    def runTest(self):
        pass

    def test_config(self):
        definition = """
sources:
  - MuOnia-2016-CF-23Sep2016-v1:
      format: root
      paths:
        - root://cmseos.fnal.gov//store/data/Run2016C/MuOnia/AOD/23Sep2016-v1/*/*.root
        - root://cmseos.fnal.gov//store/data/Run2016F/MuOnia/AOD/23Sep2016-v1/*/*.root

  - MuOnia-2016-CF-PromptReco-v2:
      format: root
      paths:
        - root://cmseos.fnal.gov//store/data/Run2016C/MuOnia/AOD/PromptReco-v2/*/*.root
        - root://cmseos.fnal.gov//store/data/Run2016F/MuOnia/AOD/PromptReco-v2/*/*.root

dataset:
  name: MuOnia

  sources:
    - MuOnia-2016C
    - MuOnia-2016F

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
            source:
              data: patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
              size: patMuons_slimmedMuons__PAT.obj
              dtype: float64
          eta:
            type: double
            source:
              data: patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fEta
              size: patMuons_slimmedMuons__PAT.obj
              dtype: float64
          phi:
            type: double
            min: -pi
            max: pi
            source:
              data: patMuons_slimmedMuons__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi
              size: patMuons_slimmedMuons__PAT.obj
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
            source:
              data: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPt
              size: patJets_slimmedJets__PAT.obj
              dtype: float64
          eta:
            type: double
            source:
              data: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fEta
              size: patJets_slimmedJets__PAT.obj
              dtype: float64
          phi:
            type: double
            min: -pi
            max: pi
            source:
              data: patJets_slimmedJets__PAT.obj.m_state.p4Polar_.fCoordinates.fPhi
              size: patJets_slimmedJets__PAT.obj
              dtype: float64
"""

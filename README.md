# Femtocode

## Introduction

Femtocode is a language and a system to support fast queries of structured data, such as high-energy physics data.

The goal is to replace the practice of copying and reducing a centrally produced dataset with direct queries on that dataset. Currently, high-energy physicists write programs to extract the attributes and data records of interest— and then have to manage the storage and versioning of that private copy— just to make plots from the subset in real time. Femtocode will allow users to make plots from the original dataset in real time, which may scale to petabytes.

Femtocode makes this possible by introducing a novel translation of query semantics into pure array operations, which strips away all unnecessary work at runtime. By dramatically reducing the computation time, only data transfer is left as the bottleneck, so caching is also heavily used to minimize the impact of repeated queries.

The project is in an early stage of development, but past the feasibility studies and basic implementation. End-to-end demonstrations will be possible by the end of April and usable prototypes sometime in the summer of 2017.

## Installation

Don’t bother yet. See above.

# Project details

## Query language

## Fast execution

## Modular backends

## Server

<img src="docs/distributed-system-simplified.png" width="100%">

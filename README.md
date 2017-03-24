# Femtocode

## Introduction

Femtocode is a language and a system to support fast queries of structured data, such as high-energy physics data.

The goal is to replace the practice of copying and reducing a centrally produced dataset with direct queries on that dataset. Currently, high-energy physicists write programs to extract the attributes and data records of interest— personally managing the storage and versioning of that private copy— just to make plots from the subset in real time. Femtocode will allow users to make plots from the original dataset in real time, which may scale to petabytes.

Femtocode makes this possible by introducing a novel translation of query semantics into pure array operations, which strips away all unnecessary work at runtime. By dramatically reducing the computation time, the only bottleneck left is the data transfer, so caching is also heavily used to minimize the impact of similar queries.

This project is in an early stage of its development, though it is past the feasibility studies and basic implementation. End-to-end demonstrations will be possible by the end of April and usable prototypes will be available sometime in the summer of 2017.

## Installation

Don’t bother yet. See above.

# Project details

## Query language

<img src="docs/explode.png" width="200" alt="Explode function">

<img src="docs/flat.png" width="200" alt="Flat function">

<img src="docs/reduce.png" width="200" alt="Reduce function">





## Fast execution

## Modular backends

## Server

<img src="docs/distributed-system-simplified.png" width="100%" alt="Schematic of query processing">

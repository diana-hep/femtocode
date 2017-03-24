# Femtocode

## Introduction

Femtocode is a language and a system to support fast queries on structured data, such as high-energy physics data.

The goal of this project is to replace the practice of copying and reducing a centrally produced dataset with direct queries on that dataset. Currently, high-energy physicists write programs to extract the attributes and data records of interest— personally managing the storage and versioning of that private copy— just to make plots from the subset in real time. Femtocode will allow users to make plots from the original dataset in real time, which may be as large as petabytes.

Femtocode makes this possible by introducing a novel translation of query semantics into pure array operations, which strips away all unnecessary work at runtime. By dramatically reducing the computation time, the only bottleneck left is the data transfer, so caching is also heavily used to minimize the impact of repeated and similar queries.

This project is at an early stage of its development, though it is past the feasibility studies and basic implementation. End-to-end demonstrations will be possible by the end of April and usable prototypes will be available sometime in the summer of 2017.

## Installation

Don’t bother yet. See above.

## Query language motivation

Femtocode was inspired by fast SQL services that translate users’ requests into operations with the same meaning as the their queries, yet are much faster than naive interpretations of them. The ability to perform these translations is helped by the fact that SQL minimally constrains the computation: there are no “for” loops to specify an order of iteration, no mutable variables, etc. The language is fast _because_ it is high-level, rather than in spite of being high-level.

At first, it would seem that SQL would be ideal for the first phase of every high-energy physics analysis: reducing huge sets of data points into distributions (histograms). But in their original form, these “data points” are structured collections of events containing jets containing tracks containing hits, all arbitrary-length lists of multi-field records. As a language, SQL does not express explode-operate-recombine tasks easily and most SQL implementations cannot evaluate them without expensive joins.

Femtocode generalizes the SELECT and WHERE parts of SQL by adding explode-operate-recombine semantics in a functional syntax. For instance, given data structured as `events >> jets >> tracks`,

    jets.map(j => j.tracks.filter(t => t.pt > 5).sum).max

would find the jet with the largest sum-of-pt for pt > 5 tracks within the jet. There would be no more than one result per event (zero if the event had no jets to start with). To do this in SQL would require assigning indexes, exploding, and then expensive joins to get one result per event. And yet it is typical of a physicist’s search through petabytes of data.

## Query Language details

To suit this application and others like it, Femtocode is

   * **declarative:** the written order of expressions is not necessarily the order evaluated,
   * **functional:** functions are objects with no side-effect generating loops or mutable variables,
   * **statically typed:** types must be understood before execution, though they are inferred from the input data types, rather than denoted explicitly,
   * **non-recursive:** no unbounded loops or infinite data are allowed,
   * **vectorizable:** the above is sufficient to allow code translations that can pipeline and vectorize similar operations, and
   * **without runtime errors:** all possible errors are caught by static analysis.

Furthermore, Femtocode’s syntax is as similar as possible to Python. Python expressions (not statements) are syntactically valid Femtocode, and Femtocode adds a more convenient lambda syntax ([see grammar](lang/generate-grammar/femtocode.g)).

Within this playground, any single-pass algorithm can be written that does not include unbounded loops: less powerful than Turing completeness but more powerful than strict SQL SELECT-WHERE. These algorithms can then be translated into sequences of operations on “shredded” data, data structures that have been flattened into featureless arrays. Rather than operating on data whose layout in memory resembles the conceptual task (e.g. all attributes of a jet together), the layout is organized for speed of access (e.g. all jet attribute `x` in one array, jet attribute `y` in another).

(See [this blog post](https://blog.twitter.com/2013/dremel-made-simple-with-parquet) for a description of shredding in Parquet. Femtocode has a slightly different shredding algorithm and performs all calculations in the shredded form, rather than just using it for efficient storage.)

Within Femtocode’s restrictions, there are only three kinds of operations: explode, flat, and combine.

#### Explode operations

<img src="docs/explode.png" width="300px" alt="Explode operation">

An array representing an attribute at one level of structure, such as one value per event, is brought in line with another array representing a different level of structure, such as one value per jet.

This can be accomplished by copying values from the first array or by moving two indexes at different rates.

#### Flat operations

<img src="docs/flat.png" width="300px" alt="Flat operation">

Two or more arrays have the same level of structure, and can therefore be operated upon element-by-element. This case corresponds to [Numpy’s “universal functions”](https://docs.scipy.org/doc/numpy/reference/ufuncs.html) or ufuncs.

Splitting loops appropriately would allow for automatic vectorization in this case, and any function adhering to the Numpy ufunc specification could be included in the language.

#### Combine operations

<img src="docs/reduce.png" width="300px" alt="Combine operation">

An array at one level of structure is reduced to a lower level of structure by computing the sum, maximum, minimum, etc. per group.

Thus, the Femtocode example

    jets.map(j => j.tracks.filter(t => t.pt > cut).sum).max

translates into

   1. Take a `cut` variable (one per event) and associate each `t.pt` value to the appropriate one (explode).
   2. Mask `t.pt` values that are greater than `cut` (flat).
   3. Compute their sum, one per jet (combine).
   4. Find the maximal jet by this measure (another combine).

Columnar operations like these can be performed considerably faster than constructing jet objects containing variable-length track collections, executing the literal code, and then deleting these objects before moving on to the next event.

In our tests, columnar operations can be performed at a rate of billions per second, mostly sensitive to hardware memory bandwidth.

<img src="docs/event_rate_knl.png" width="600px" alt="Event rate on various platforms">

Amusingly, this is about the rate at which high-energy physics collisions occur in modern colliders. These events are, however, filtered by many orders of magnitude during data acquisition, so a query system that can analyze a billion events per second would be able to plot several year’s worth of data “instantly.”

## Workflow structure

Femtocode is not and will not be a complete language in the same sense as Python or C++. The restriction on recursion and other forms of unbounded looping limit its applicability for general programming.

The intended use of Femtocode is similar to that of SQL snippets within an application, regular expressions, or ROOT’s `TTree::Draw` (familiar to physicists). It appears in quoted blocks like this (from current unit tests):

```python
session = RemoteSession("http://testserver:8080")

pending = session.source("xy-dataset")
                 .define(z = "x + y")
                 .toPython("Result", a = "z - 3", b = "z - 0.5")
                 .submit()

result = result.await()
for x in result:
    print x
```

or this (someday):

```python
workflow = session.source("b-physics")                   # pull from a named dataset
       .define(goodmuons = "muons.filter($1.pt > 5)")    # muons with pt > 5 are good
       .filter("goodmuons.size >= 2")                    # keep events with at least two
       .define(dimuon = """
           mu1, mu2 = goodmuons.maxby($1.pt, 2);         # pick the top two by pt
           energy = mu1.E + mu2.E;                       # compute combined energy/momentum
           px = mu1.px + mu2.px;
           py = mu1.py + mu2.py;
           pz = mu1.pz + mu2.pz;

           rec(mass = sqrt(energy**2 - px**2 - py**2 - pz**2),
               pt = sqrt(px**2 + py**2),
               phi = atan2(py, px),
               eta = ln((energy + pz)/(energy - pz))/2)  # construct a record as output
           """)
       .bundle(                                          # make a bundle of plots
           mass = bin(120, 0, 12, "dimuon.mass"),        # using the variables we’ve made
           pt = bin(100, 0, 100, "dimuon.pt"),
           eta = bin(100, -5, 5, "dimuon.eta"),
           phi = bin(314, 0, 2*pi, "dimuon.phi + pi"),
           muons = foreach("goodmuons", "mu", bundle(    # also make plots with one muon per entry
               pt = bin(100, 0, 100, "mu.pt"),
               eta = bin(100, -5, 5, "mu.eta"),
               phi = bin(314, -pi, pi, "mu.phi")
           ))
       )

pending = workflow.submit()                              # submit the query
pending["mass"].plot()                                   # and plot results while they accumulate
pending["muons"]["pt"].plot()                            # (they’ll be animated)

blocking = pending.await()                               # stop the code until the result is in

massplot = blocking.plot.root("mass")                    # convert to a familiar format, like ROOT
massplot.Fit("gaus")                                     # and use that package’s tools
```

A workflow describes a chain of operations to perform on the source data, ending with some sort of aggregation. The chain is strictly linear up to the aggregation step, which then branches into a tree. The aggregation step uses concepts and code from the [Histogrammar project](http://github.com/histogrammar/histogrammar-python).

Each workflow is submitted as a query to a query engine (single process or distributed server), which immediately returns a “future” object. This object monitors the progress of the query, even plotting partial results (histograms fill up with entries) so that the user can decide to cancel early.

_Why linear, and not a full directed acyclic graph (DAG)?_ DAGs are good for two things: splitting the output and explicitly short-circuting some processes to avoid unnecessary work. In our case, the aggregation step is a general tree, providing multiple outputs, so this capability is covered. As for avoiding unnecessary work, the columnar nature of the calculation undermines our ability to make per-event choices about work, and the Femtocode compilation process uses the language’s perfect referential transparency to automatically avoid calculating repeated subexpressions. Thus, full DAGs aren’t necessary.

_What about skims for unbinned fits or machine learning?_ The feasibility of the above depends on the returned results being much smaller than the input datasets, as a histogram of dimuon mass is much smaller than a collection of muon records. However, some analysis techniques need unaggregated data. They must be treated specially— for instance, the returned result would be a pointer to a remote disk on which the full skim is located.

Although we still envision the necessity of making private subsets of the data for these purposes, the user’s behavior could be turned from skim-first, plot-later to plot-first, skim-later, reducing the chance of mistakes that would require re-skims.

## Eliminating runtime errors






total functional language




## Fast execution

## Modular backends

## Query Server

<img src="docs/distributed-system-simplified.png" width="100%" alt="Schematic of query processing">

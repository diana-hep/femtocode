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

import os
import subprocess

from setuptools import setup, find_packages, Extension
import numpy.distutils.misc_util

import femtocode.version

def rootconfig(arg, filter, drop):
    rootconfig = subprocess.Popen(["root-config", arg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if rootconfig.wait() != 0:
        raise IOError(rootconfig.stderr.read())
    return [x.strip()[drop:] for x in rootconfig.stdout.read().decode().split(" ") if filter(x)]

setup(name = "femtocode-rootio",
      version = femtocode.version.__version__,
      packages = find_packages(),
      scripts = [],
      description = "",
      long_description = """""",
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "http://femtocode.org",
      download_url = "https://github.com/diana-hep/femtocode",
      license = "Apache Software License v2",
      test_suite = "tests",
      install_requires = ["femtocode", "ruamel.yaml", "numpy"],
      tests_require = [],
      classifiers = ["Development Status :: 2 - Pre-Alpha",
                     # "Development Status :: 5 - Production/Stable",   # no way!
                     "Environment :: Console",
                     "Intended Audience :: Science/Research",
                     "License :: OSI Approved :: Apache Software License",
                     "Topic :: Scientific/Engineering :: Information Analysis",
                     "Topic :: Scientific/Engineering :: Mathematics",
                     "Topic :: Scientific/Engineering :: Physics",
                     ],
      platforms = "Any",
      ext_modules = [Extension("femtocode.rootio._fastreader",
                               [os.path.join("femtocode", "rootio", "_fastreader.cpp")],
                               include_dirs = rootconfig("--cflags", lambda x: x.startswith("-I"), 2) + numpy.distutils.misc_util.get_numpy_include_dirs(),
                               library_dirs = rootconfig("--libdir", lambda x: True, 0),
                               libraries = rootconfig("--libs", lambda x: x.startswith("-l"), 2),
                               extra_compile_args = rootconfig("--cflags", lambda x: not x.startswith("-I"), 0),
                               )],
      )

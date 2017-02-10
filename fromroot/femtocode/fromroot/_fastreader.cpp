// Copyright 2016 DIANA-HEP
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <iostream>
#include <vector>
#include <string>

#include <Python.h>
#include <numpy/arrayobject.h>

#include <TFile.h>
#include <TTree.h>
#include <TLeaf.h>
#include <TBranchElement.h>

static char module_docstring[] = "Simple, streamlined Numpy array-filling from ROOT.";
static char fillarrays_docstring[] = "Fills N arrays at once from a ROOT file's TTree.\n\nparams:\n    fileName: string, can include root:// protocol\n    ttreeName: string, can include directory slashes\n    arrays: list of (string, Numpy array) tuples; first element is TBranch name, second is a preallocated array.\n\nRaises IndexError if more values are found in the ROOT file than are allocated in the array.";

static PyObject* fillarrays(PyObject* self, PyObject* args);

static PyMethodDef module_methods[] = {
  {"fillarrays", (PyCFunction)fillarrays, METH_VARARGS, fillarrays_docstring},
  {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "_fastreader",
  NULL,
  0,
  module_methods,
  NULL,
  NULL,
  NULL,
  NULL
};

PyMODINIT_FUNC PyInit__fastreader(void) {
  PyObject* module = PyModule_Create(&moduledef);
  if (module != NULL)
    import_array();
  return module;
}
#else
PyMODINIT_FUNC init_fastreader(void) {
  PyObject* module = Py_InitModule3("_fastreader", module_methods, module_docstring);
  if (module != NULL)
    import_array();
}
#endif

static PyObject* fillarrays(PyObject* self, PyObject* args) {
  char* fileName;
  char* treeName;
  PyObject* branches_arrays;

  if (!PyArg_ParseTuple(args, "ssO", &fileName, &treeName, &branches_arrays))
    return NULL;

  if (!PySequence_Check(branches_arrays)) {
    PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) pairs");
    return NULL;
  }

  int numArrays = PySequence_Length(branches_arrays);
  std::vector<std::string> branchNames;
  std::vector<char> arrayTypes;
  std::vector<int> arrayItemSizes;
  std::vector<int> arraySizes;

  for (Py_ssize_t i = 0;  i < numArrays;  i++) {
    // Doesn't need to be fast, but this returns a borrowed reference, which is nice because I don't have to handle references.
    PyObject* pair = PySequence_Fast_GET_ITEM(branches_arrays, i);
    if (!PyTuple_Check(pair)) {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) pairs");
      return NULL;
    }

    char* branchName;
    PyObject* array;
    if (!PyArg_ParseTuple(pair, "sO", &branchName, &array)) {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) pairs");
      return NULL;
    }

    if (!PyArray_Check(array)) {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) pairs");
      return NULL;
    }

    PyArray_Descr* dtype = PyArray_DESCR(array);

    int ndim = PyArray_NDIM(array);
    if (ndim != 1) {
      PyErr_SetString(PyExc_TypeError, "arrays must be one-dimensional");
      return NULL;
    }

    npy_intp size = PyArray_DIM(array, 0);

    switch (dtype->type) {
    case 'B':  // numpy.uint8
    case 'd':  // numpy.float64
    case 'l':  // numpy.int64
    case 'L':  // numpy.uint64
    case 'f':  // numpy.float32
    case 'i':  // numpy.int32
    case 'I':  // numpy.uint32
      break;
    default:
      PyErr_SetString(PyExc_TypeError, "array dtype not supported (only uint8, float64, int64, uint64, float32, int32, uint32)");
      return NULL;
    }

    branchNames.push_back(std::string(branchName));
    arrayTypes.push_back(dtype->type);
    arrayItemSizes.push_back(dtype->elsize);
    arraySizes.push_back(size);
  }

  // Are these references new? borrowed? stolen?
  TFile* tfile = TFile::Open(fileName);
  TTree* ttree;
  tfile->GetObject(treeName, ttree);
  if (ttree == NULL) {
    PyErr_SetString(PyExc_IOError, "bad or missing TTree");
    return NULL;
  }

  std::vector<TBranchElement*> branchElements;
  for (int i = 0;  i < numArrays;  i++) {
    TBranchElement *branch = (TBranchElement*)ttree->GetBranch(branchNames[i].c_str());
    if (branch == NULL) {
      PyErr_SetString(PyExc_IOError, "bad or missing TBranch");
      return NULL;
    }
  }








  return Py_BuildValue("O", Py_None);
}

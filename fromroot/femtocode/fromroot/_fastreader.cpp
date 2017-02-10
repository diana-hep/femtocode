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
#include <TError.h>
#include <TTree.h>
#include <TLeaf.h>
#include <TBranch.h>
#include <TBranchElement.h>

static char module_docstring[] = "Simple, streamlined Numpy array-filling from ROOT.";
static char fillarrays_docstring[] = "Fills N arrays at once from a ROOT file's TTree.\n\nparams:\n    fileName: string, can include root:// protocol\n    ttreeName: string, can include directory slashes\n    arrays: list of (string, array) or (string, string, array, array) tuples: (data name, data array) or (data name, size name, data array, size array). Arrays must be preallocated.\n\nRaises IndexError if more values are found in the ROOT file than are allocated in the array.";

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

class BranchArrayInfo {
public:
  TBranch* dataBranch;
  char* bufferForEntry;
  Int_t sizeForEntry;

  char* dataName;
  char* sizeName;
  int64_t dataLength;
  int64_t sizeLength;
  char dataType;
  int dataItemBytes;
  bool flat;

  BranchArrayInfo(char* dataName, char* sizeName, int64_t dataLength, int64_t sizeLength, char dataType, int dataItemBytes, bool flat):
    dataBranch(NULL), bufferForEntry(NULL), sizeForEntry(0),
    dataName(dataName), sizeName(sizeName), dataLength(dataLength), sizeLength(sizeLength), dataType(dataType), dataItemBytes(dataItemBytes), flat(flat) { }

  ~BranchArrayInfo() {
    if (bufferForEntry != NULL) delete bufferForEntry;
  }
};

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
  std::vector<BranchArrayInfo> branchArrayInfos;

  for (Py_ssize_t i = 0;  i < numArrays;  i++) {
    // Doesn't need to be fast, but PySequence_Fast_GET_ITEM returns a borrowed reference, which is nice because I don't have to handle references.
    PyObject* branch_array = PySequence_Fast_GET_ITEM(branches_arrays, i);
    if (!PyTuple_Check(branch_array)) {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) or (string, string, array, array) tuples");
      return NULL;
    }

    PyObject* dataArray;
    PyObject* sizeArray;

    char* dataName;
    char* sizeName;
    int64_t dataLength;
    int64_t sizeLength;
    char dataType;
    int dataItemBytes;
    bool flat;

    if (PySequence_Size(branch_array) == 2)
      flat = true;
    else if (PySequence_Size(branch_array) == 4)
      flat = false;
    else {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) or (string, string, array, array) tuples");
      return NULL;
    }

    if (flat) {
      if (!PyArg_ParseTuple(branch_array, "sO", &dataName, &dataArray)) {
        PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) or (string, string, array, array) tuples");
        return NULL;
      }
      sizeName = NULL;
      sizeArray = NULL;
      sizeLength = 0;
    }
    else {
      if (!PyArg_ParseTuple(branch_array, "ssOO", &dataName, &sizeName, &dataArray, &sizeArray)) {
        PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) or (string, string, array, array) tuples");
        return NULL;
      }

      int ndim = PyArray_NDIM(sizeArray);
      if (ndim != 1) {
        PyErr_SetString(PyExc_TypeError, "size arrays must be one-dimensional");
        return NULL;
      }
      sizeLength = PyArray_DIM(sizeArray, 0);
    }

    int ndim = PyArray_NDIM(dataArray);
    if (ndim != 1) {
      PyErr_SetString(PyExc_TypeError, "data arrays must be one-dimensional");
      return NULL;
    }
    dataLength = PyArray_DIM(dataArray, 0);

    dataType = PyArray_DESCR(dataArray)->type;
    switch (dataType) {
    case 'B':  // numpy.uint8
    case 'd':  // numpy.float64
    case 'l':  // numpy.int64
    case 'L':  // numpy.uint64
    case 'f':  // numpy.float32
    case 'i':  // numpy.int32
    case 'I':  // numpy.uint32
      break;
    default:
      PyErr_SetString(PyExc_TypeError, "data dtype not supported (only uint8, float64, int64, uint64, float32, int32, uint32)");
      return NULL;
    }

    dataItemBytes = PyArray_DESCR(dataArray)->elsize;

    branchArrayInfos.push_back(BranchArrayInfo(dataName, sizeName, dataLength, sizeLength, dataType, dataItemBytes, flat));
  }

  // FIXME: Are the ROOT references new? borrowed? stolen?

  Int_t oldLevel = gErrorIgnoreLevel;   // error message suppression is not thread safe
  gErrorIgnoreLevel = kError;           // but oh well...
  TFile* tfile = TFile::Open(fileName);
  gErrorIgnoreLevel = oldLevel;         // FIXME: turn off more selectively?

  TTree* ttree;
  tfile->GetObject(treeName, ttree);
  if (ttree == NULL) {
    PyErr_SetString(PyExc_IOError, "bad or missing TTree");
    return NULL;
  }

  std::cout << "ONE" << std::endl;

  for (int i = 0;  i < numArrays;  i++) {
    TBranch* dataBranch = ttree->GetBranch(branchArrayInfos[i].dataName);
    if (dataBranch == NULL) {
      PyErr_SetString(PyExc_IOError, "bad or missing TBranch");
      return NULL;
    }
    branchArrayInfos[i].dataBranch = dataBranch;
  }

  std::cout << "TWO" << std::endl;

  // fragile: the placement of this function call matters
  ttree->SetMakeClass(1);

  std::cout << "THREE" << std::endl;

  for (int i = 0;  i < numArrays;  i++) {
    if (branchArrayInfos[i].flat) {
      // FIXME: implement flat
      PyErr_SetString(PyExc_NotImplementedError, "flat column");
      return NULL;
    }
    else {
      std::cout << "FOUR" << std::endl;

      if (!branchArrayInfos[i].dataBranch->IsA()->InheritsFrom("TBranchElement")) {
        PyErr_SetString(PyExc_IOError, "non-flat data should be a TBranchElement");
        return NULL;
      }

      std::cout << "FIVE" << std::endl;

      TBranchElement *branchElement = (TBranchElement*)branchArrayInfos[i].dataBranch;

      std::cout << "SIX" << std::endl;

      int bufferSize = ((TLeaf*)(branchElement->GetListOfLeaves()->First()))->GetLeafCount()->GetMaximum();

      std::cout << "SEVEN" << std::endl;

      branchArrayInfos[i].bufferForEntry = new char[bufferSize * branchArrayInfos[i].dataItemBytes];

      std::cout << "EIGHT" << std::endl;

      ttree->SetBranchAddress(branchArrayInfos[i].dataName, branchArrayInfos[i].bufferForEntry);

      std::cout << "NINE" << std::endl;

      ttree->SetBranchAddress(branchArrayInfos[i].sizeName, &(branchArrayInfos[i].sizeForEntry));

      std::cout << "TEN" << std::endl;
    }
  }







  return Py_BuildValue("O", Py_None);
}

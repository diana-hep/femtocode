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
static char fillarrays_docstring[] = "Fills N arrays at once from a ROOT file's TTree.\n\nparams:\n    fileName: string, can include root:// protocol\n    ttreeName: string, can include directory slashes\n    arrays: list of (string, array) or (string, string, array, array) tuples: (data name, data array) or (data name, size name, data array, size array). Arrays must be preallocated or pass None just to get the allocation size.\n\nreturns:\n    tuple of N+1 ints: total number of entries followed by the total number of each object.\n\nraises:\n    IndexError if more values are found in the ROOT file than are allocated in the array.";
static char getsize_docstring[] = "Get size branch names for each data branch.\n\nparams:\n    fileName: string, can include root:// protocol\n    ttreeName: string, can include directory slashes\n    data: list of string names.\n\nreturns:\n    list (same length) of size branch names with None if the branch is flat.\n\nraises:\n    IOError if any branch is not found.";

static PyObject* fillarrays(PyObject* self, PyObject* args);
static PyObject* getsize(PyObject* self, PyObject* args);

static PyMethodDef module_methods[] = {
  {"fillarrays", (PyCFunction)fillarrays, METH_VARARGS, fillarrays_docstring},
  {"getsize", (PyCFunction)getsize, METH_VARARGS, getsize_docstring},
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
  uint64_t dataIndex;
  uint64_t sizeIndex;
  TBranch* dataBranch;
  char* bufferForEntry;
  Int_t sizeForEntry;

  void* dataPointer;
  void* sizePointer;
  char* dataName;
  char* sizeName;
  uint64_t dataLength;
  uint64_t sizeLength;
  int whichSize;
  char dataType;
  bool flat;

  BranchArrayInfo(void* dataPointer, void* sizePointer, char* dataName, char* sizeName, uint64_t dataLength, int64_t sizeLength, char dataType, bool flat, int whichSize):
    dataIndex(0),
    sizeIndex(0),
    dataBranch(NULL),
    bufferForEntry(NULL),
    sizeForEntry(0),
    dataPointer(dataPointer),
    sizePointer(sizePointer),
    dataName(dataName),
    sizeName(sizeName),
    dataLength(dataLength),
    sizeLength(sizeLength),
    whichSize(whichSize),
    dataType(dataType),
    flat(flat) { }

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
  int numArraysToLoad = 0;
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

    void* dataPointer;
    void* sizePointer;
    char* dataName;
    char* sizeName;
    uint64_t dataLength;
    uint64_t sizeLength;
    char dataType;
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
      sizePointer = NULL;
      sizeName = NULL;
      sizeArray = NULL;
      sizeLength = 0;
    }
    else {
      if (!PyArg_ParseTuple(branch_array, "ssOO", &dataName, &sizeName, &dataArray, &sizeArray)) {
        PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) or (string, string, array, array) tuples");
        return NULL;
      }

      if (sizeArray == Py_None) {
        sizePointer = NULL;
        sizeLength = 0;
      }
      else if (PyArray_Check(sizeArray)) {
        sizePointer = PyArray_DATA(sizeArray);

        int ndim = PyArray_NDIM(sizeArray);
        if (ndim != 1) {
          PyErr_SetString(PyExc_TypeError, "size arrays must be one-dimensional");
          return NULL;
        }
        sizeLength = PyArray_DIM(sizeArray, 0);

        if (PyArray_DESCR(sizeArray)->type != 'L') {
          PyErr_SetString(PyExc_TypeError, "size arrays must be uint64");
          return NULL;
        }
      }
      else {
        PyErr_SetString(PyExc_TypeError, "size array must be a Numpy array or None");
        return NULL;
      }
    }

    int whichSize = i;
    if (dataArray == Py_None) {
      dataPointer = NULL;
      dataLength = 0;
      dataType = '?';
    }
    else if (PyArray_Check(dataArray)) {
      dataPointer = PyArray_DATA(dataArray);

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

      for (int j = 0;  j < i;  j++)
        if (sizePointer != NULL  &&  sizePointer == branchArrayInfos[j].sizePointer) {
          whichSize = j;
          break;
        }
    }
    else {
      PyErr_SetString(PyExc_TypeError, "data array must be a Numpy or None");
      return NULL;
    }

    if (dataPointer != NULL  ||  sizeName != NULL)
      numArraysToLoad++;
   
    branchArrayInfos.push_back(BranchArrayInfo(dataPointer, sizePointer, dataName, sizeName, dataLength, sizeLength, dataType, flat, whichSize));
  }

  PyThreadState *_save;
  _save = PyEval_SaveThread();

  // FIXME: Are the ROOT references new? borrowed? stolen?

  Int_t oldLevel = gErrorIgnoreLevel;   // error message suppression is not thread safe
  gErrorIgnoreLevel = kError;           // but oh well...
  TFile* tfile = TFile::Open(fileName);
  gErrorIgnoreLevel = oldLevel;         // FIXME: turn off more selectively?

  if (tfile == NULL  ||  !tfile->IsOpen()) {
    PyEval_RestoreThread(_save);
    PyErr_SetString(PyExc_IOError, "could not open file");
    return NULL;
  }

  TTree* ttree;
  tfile->GetObject(treeName, ttree);
  if (ttree == NULL) {
    PyEval_RestoreThread(_save);
    PyErr_SetString(PyExc_IOError, "bad or missing TTree");
    return NULL;
  }

  for (int i = 0;  i < numArrays;  i++) {
    TBranch* dataBranch = ttree->GetBranch(branchArrayInfos[i].dataName);
    if (dataBranch == NULL) {
      PyEval_RestoreThread(_save);
      PyErr_SetString(PyExc_IOError, "bad or missing TBranch");
      return NULL;
    }
    branchArrayInfos[i].dataBranch = dataBranch;
  }

  // fragile: the placement of this function call matters
  ttree->SetMakeClass(1);

  for (int i = 0;  i < numArrays;  i++) {
    int dataItemBytes = ((TLeaf*)(branchArrayInfos[i].dataBranch->GetListOfLeaves()->First()))->GetLenType();

    if (branchArrayInfos[i].flat) {
      branchArrayInfos[i].bufferForEntry = new char[2 * dataItemBytes];

      ttree->SetBranchAddress(branchArrayInfos[i].dataName, branchArrayInfos[i].bufferForEntry);
    }

    else {
      if (!branchArrayInfos[i].dataBranch->IsA()->InheritsFrom("TBranchElement")) {
        PyEval_RestoreThread(_save);
        PyErr_SetString(PyExc_IOError, "non-flat data should be a TBranchElement");
        return NULL;
      }
      TBranchElement *branchElement = (TBranchElement*)branchArrayInfos[i].dataBranch;

      int bufferSize = ((TLeaf*)(branchElement->GetListOfLeaves()->First()))->GetLeafCount()->GetMaximum();
      branchArrayInfos[i].bufferForEntry = new char[bufferSize * 2 * dataItemBytes];

      ttree->SetBranchAddress(branchArrayInfos[i].dataName, branchArrayInfos[i].bufferForEntry);
      if (branchArrayInfos[i].whichSize == i)
        ttree->SetBranchAddress(branchArrayInfos[i].sizeName, &(branchArrayInfos[i].sizeForEntry));
    }
  }

  Long64_t numEntries = ttree->GetEntries();
  Long64_t entry;
  int i;
  uint64_t item;
  uint64_t sizeForEntry = 0;

  if (numArraysToLoad > 0) {
    for (entry = 0;  entry < numEntries;  entry++) {
      for (i = 0;  i < numArrays;  i++) {
        branchArrayInfos[i].dataBranch->GetEntry(entry);

        if (branchArrayInfos[i].dataPointer == NULL) {
          branchArrayInfos[i].dataLength += branchArrayInfos[branchArrayInfos[i].whichSize].sizeForEntry;
        }
        else {
          if (branchArrayInfos[i].flat) {
            if (branchArrayInfos[i].dataIndex < branchArrayInfos[i].dataLength) {
              switch (branchArrayInfos[i].dataType) {
              case 'B':  // numpy.uint8
                ((uint8_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((uint8_t*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              case 'd':  // numpy.float64
                ((double*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((double*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              case 'l':  // numpy.int64
                ((int64_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((int64_t*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              case 'L':  // numpy.uint64
                ((uint64_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((uint64_t*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              case 'f':  // numpy.float32
                ((float*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((float*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              case 'i':  // numpy.int32
                ((int32_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((int32_t*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              case 'I':  // numpy.uint32
                ((uint32_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((uint32_t*)branchArrayInfos[i].bufferForEntry)[0];
                break;
              }
            }
            else {
              PyEval_RestoreThread(_save);
              PyErr_SetString(PyExc_IOError, "ROOT file data is bigger than data array");
              return NULL;
            }
          }

          else {
            sizeForEntry = branchArrayInfos[branchArrayInfos[i].whichSize].sizeForEntry;

            if (branchArrayInfos[i].whichSize == i) {
              if (branchArrayInfos[i].sizePointer != NULL) {
                if (branchArrayInfos[i].sizeIndex < branchArrayInfos[i].sizeLength)
                  ((uint64_t*)(branchArrayInfos[i].sizePointer))[branchArrayInfos[i].sizeIndex++] = sizeForEntry;
                else {
                  PyEval_RestoreThread(_save);
                  PyErr_SetString(PyExc_IOError, "ROOT file size is bigger than size array");
                  return NULL;
                }
              }
            }

            for (item = 0;  item < sizeForEntry;  item++) {
              if (branchArrayInfos[i].dataIndex < branchArrayInfos[i].dataLength) {
                switch (branchArrayInfos[i].dataType) {
                case 'B':  // numpy.uint8
                  ((uint8_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((uint8_t*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                case 'd':  // numpy.float64
                  ((double*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((double*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                case 'l':  // numpy.int64
                  ((int64_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((int64_t*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                case 'L':  // numpy.uint64
                  ((uint64_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((uint64_t*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                case 'f':  // numpy.float32
                  ((float*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((float*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                case 'i':  // numpy.int32
                  ((int32_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((int32_t*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                case 'I':  // numpy.uint32
                  ((uint32_t*)(branchArrayInfos[i].dataPointer))[branchArrayInfos[i].dataIndex++] = ((uint32_t*)branchArrayInfos[i].bufferForEntry)[item];
                  break;
                }
              }
              else {
                PyEval_RestoreThread(_save);
                PyErr_SetString(PyExc_IOError, "ROOT file data is bigger than data array");
                return NULL;
              }
            }
          }
        }
      }
    }
  }

  PyEval_RestoreThread(_save);

  PyObject* out = PyTuple_New(numArrays + 1);
  if (PyTuple_SetItem(out, 0, PyLong_FromLong(numEntries)) != 0) {
    PyErr_SetString(PyExc_IOError, "could not fill output tuple");
    return NULL;
  }
  for (i = 0;  i < numArrays;  i++) {
    if (PyTuple_SetItem(out, i + 1, PyLong_FromLong(branchArrayInfos[i].dataLength)) != 0) {
      PyErr_SetString(PyExc_IOError, "could not fill output tuple");
      return NULL;
    }
  }

  return out;
}

static PyObject* getsize(PyObject* self, PyObject* args) {
  char* fileName;
  char* treeName;
  PyObject* branches;

  if (!PyArg_ParseTuple(args, "ssO", &fileName, &treeName, &branches))
    return NULL;

  if (!PySequence_Check(branches)) {
    PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of strings");
    return NULL;
  }
  int numBranches = PySequence_Length(branches);

  Int_t oldLevel = gErrorIgnoreLevel;   // error message suppression is not thread safe
  gErrorIgnoreLevel = kError;           // but oh well...
  TFile* tfile = TFile::Open(fileName);
  gErrorIgnoreLevel = oldLevel;         // FIXME: turn off more selectively?

  if (tfile == NULL  ||  !tfile->IsOpen()) {
    PyErr_SetString(PyExc_IOError, "could not open file");
    return NULL;
  }

  TTree* ttree;
  tfile->GetObject(treeName, ttree);
  if (ttree == NULL) {
    PyErr_SetString(PyExc_IOError, "bad or missing TTree");
    return NULL;
  }

  PyObject* out = PyList_New(numBranches);

  for (Py_ssize_t i = 0;  i < numBranches;  i++) {
    PyObject* pyDataName = PySequence_Fast_GET_ITEM(branches, i);
    const char* dataName;

#if PY_MAJOR_VERSION >= 3
    if (PyBytes_Check(pyDataName))
      dataName = PyBytes_AsString(pyDataName);
    else if (PyUnicode_Check(pyDataName))
      dataName = PyUnicode_AsUTF8AndSize(pyDataName, NULL);
    else {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of strings");
      return NULL;
    }
#else
    if (PyString_Check(pyDataName))
      dataName = PyString_AsString(pyDataName);
    else {
      PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of strings");
      return NULL;
    }
#endif

    TBranch* tbranch = ttree->GetBranch(dataName);

    if (tbranch == NULL) {
      std::string err = std::string("TFile \"") + std::string(fileName) + std::string("\", TTree \"") + std::string(treeName) + std::string("\" does not have TBranch \"") + std::string(dataName) + std::string("\"");
      PyErr_SetString(PyExc_IOError, err.c_str());
      return NULL;
    }

    bool filled = false;
    if (tbranch->IsA()->InheritsFrom("TBranchElement")) {
      TLeaf* counter = ((TLeaf*)(tbranch->GetListOfLeaves()->First()))->GetLeafCount();

      if (counter != NULL) {
        const char* sizeName = counter->GetBranch()->GetName();

#if PY_MAJOR_VERSION >= 3
        PyObject* pySizeName = PyUnicode_FromString(sizeName);
#else
        PyObject* pySizeName = PyString_FromString(sizeName);
#endif

        if (pySizeName == NULL  ||  PyList_SetItem(out, i, pySizeName) != 0) {
          PyErr_SetString(PyExc_RuntimeError, "could not fill output");
          return NULL;
        }
        filled = true;
      }
    }

    if (!filled) {
      if (PyList_SetItem(out, i, Py_BuildValue("O", Py_None)) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "could not fill output");
        return NULL;
      }
    }
  }

  return out;
}

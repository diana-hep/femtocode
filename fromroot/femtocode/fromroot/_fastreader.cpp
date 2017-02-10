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

#include <Python.h>
#include <numpy/arrayobject.h>

#include <TFile.h>

static char module_docstring[] = "Simple, streamlined Numpy array-filling from ROOT.";
static char fillarrays_docstring[] = "Fills N arrays at once from a ROOT file's TTree.\n\nparams:\n    fileName: string, can include root:// protocol\n    ttreeName: string, can include directory slashes\n    arrays: list of (string, Numpy array) tuples; first element is TBranch name, second is a preallocated array.\n\nRaises IndexError if more values are found in the ROOT file than are allocated in the array.";

static PyObject *fillarrays(PyObject *self, PyObject *args);

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
  PyObject *module = PyModule_Create(&moduledef);
  if (module != NULL)
    import_array();
  return module;
}
#else
PyMODINIT_FUNC init_fastreader(void) {
  PyObject *module = Py_InitModule3("_fastreader", module_methods, module_docstring);
  if (module != NULL)
    import_array();
}
#endif

static PyObject *fillarrays(PyObject *self, PyObject *args) {
  char* fileName;
  char* treeName;
  PyObject *branches_arrays;

  if (!PyArg_ParseTuple(args, "ssO", &fileName, &treeName, &branches_arrays))
    return NULL;

  std::cout << "HERE " << fileName << " " << treeName << std::endl;

  if (!PySequence_Check(branches_arrays)) {
    PyErr_SetString(PyExc_TypeError, "third argument must be a sequence of (string, array) pairs");
    return NULL;
  }

  for (Py_ssize_t i = 0;  i < PySequence_Length(branches_arrays);  i++) {
    std::cout << "WOWIE" << std::endl;
  }



  return Py_BuildValue("O", Py_None);
}

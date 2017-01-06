/*************************************************************************

Copyright 2016 DIANA-HEP

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

*************************************************************************/

#include <stdlib.h>
#include <stdio.h>

#include "femtocoderun.h"

void explodesize_entry(LevelIndex numLevels, ColumnIndex numSizeColumns, LevelIndex levi, ColumnIndex* levelToColumnIndex, ArrayIndex* si, ArrayIndex* startsi, ItemCount** sizeColumns, ArrayIndex* explodedlen, ItemCount* exploded) {
  if (levi == numLevels) {
    printf(".");
  }
  else {
    ColumnIndex coli = levelToColumnIndex[levi];
    ItemCount repeat = sizeColumns[coli][si[coli]];
    ItemCount i;
    ColumnIndex j;
    si[coli]++;

    if (exploded != NULL)
      exploded[(*explodedlen)] = repeat;
    (*explodedlen)++;

    for (j = 0;  j < numSizeColumns;  j++)
      startsi[levi * numSizeColumns + j] = si[j];

    printf("[");
    for (i = 0;  i < repeat;  i++) {
      for (j = 0;  j < numSizeColumns;  j++)
        if (j != coli)
          si[j] = startsi[levi * numSizeColumns + j];

      explodesize_entry(numLevels, numSizeColumns, levi + 1, levelToColumnIndex, si, startsi, sizeColumns, explodedlen, exploded);
    }
    printf("]");
  }
}

ArrayIndex explodesize(EntryCount numEntries, LevelIndex numLevels, ColumnIndex numSizeColumns, ColumnIndex* levelToColumnIndex, ItemCount** sizeColumns, ItemCount* exploded) {
  uint32_t* indexes = malloc((numLevels + 2*numSizeColumns + 2*numLevels*numSizeColumns) * sizeof(uint32_t));
  ColumnIndex* levelToColumnIndex2;
  ArrayIndex* si;
  ArrayIndex* startsi;
  uint32_t i;
  ArrayIndex explodedlen = 0;
  EntryCount entry;

  levelToColumnIndex2 = &indexes[0];
  for (i = 0;  i < numLevels;  i++) levelToColumnIndex2[i] = levelToColumnIndex[i];

  si = (ArrayIndex*)&indexes[numLevels];
  for (i = 0;  i < numSizeColumns;  i++) si[i] = 0;

  startsi = (ArrayIndex*)&indexes[numLevels + 2*numSizeColumns];

  for (entry = 0;  entry < numEntries;  entry++) {
    explodesize_entry(numLevels, numSizeColumns, 0, levelToColumnIndex2, si, startsi, sizeColumns, &explodedlen, exploded);
    printf("\n");
  }

  free(indexes);
  return explodedlen;
}

void explodedata_entry(LevelIndex numLevels, ColumnIndex numSizeColumns, LevelIndex levi, ColumnIndex* levelToColumnIndex, ArrayIndex* si, ArrayIndex* startsi, ArrayIndex* di, ArrayIndex* startdi, ItemCount** sizeColumns, ColumnIndex dataSizeColumn, NumBytes datumBytes, char* data, ArrayIndex* explodedlen, char* exploded) {
  if (levi == numLevels) {
    printf(".");

    if (exploded != NULL) {
      NumBytes j;
      for (j = 0;  j < datumBytes;  j++)
        exploded[(*explodedlen) * datumBytes + j] = data[(*di) * datumBytes + j];
    }
    (*explodedlen)++;
    (*di)++;
  }
  else {
    ColumnIndex coli = levelToColumnIndex[levi];
    ItemCount repeat = sizeColumns[coli][si[coli]];
    ItemCount i;
    ColumnIndex j;
    si[coli]++;

    for (j = 0;  j < numSizeColumns;  j++)
      startsi[levi * numSizeColumns + j] = si[j];
    startdi[levi] = *di;

    printf("[");
    for (i = 0;  i < repeat;  i++) {
      for (j = 0;  j < numSizeColumns;  j++)
        if (j != coli)
          si[j] = startsi[levi * numSizeColumns + j];

      if (dataSizeColumn != coli)
        *di = startdi[levi];

      explodedata_entry(numLevels, numSizeColumns, levi + 1, levelToColumnIndex, si, startsi, di, startdi, sizeColumns, dataSizeColumn, datumBytes, data, explodedlen, exploded);
    }
    printf("]");
  }
}

ArrayIndex explodedata(EntryCount numEntries, LevelIndex numLevels, ColumnIndex numSizeColumns, ColumnIndex* levelToColumnIndex, ItemCount** sizeColumns, ColumnIndex dataSizeColumn, NumBytes datumBytes, void* data, void* exploded) {
  uint32_t* indexes = malloc((numLevels + 2*numSizeColumns + 2*numLevels*numSizeColumns + 2*numLevels) * sizeof(uint32_t));
  ColumnIndex* levelToColumnIndex2 = &indexes[0];
  ArrayIndex* si;
  ArrayIndex* startsi;
  ArrayIndex di = 0;
  ArrayIndex* startdi;
  uint32_t i;
  ArrayIndex explodedlen = 0;
  EntryCount entry;

  for (i = 0;  i < numLevels;  i++) levelToColumnIndex2[i] = levelToColumnIndex[i];

  si = (ArrayIndex*)&indexes[numLevels];
  for (i = 0;  i < numSizeColumns;  i++) si[i] = 0;

  startsi = (ArrayIndex*)&indexes[numLevels + 2*numSizeColumns];
  startdi = (ArrayIndex*)&indexes[numLevels + 2*numSizeColumns + 2*numLevels*numSizeColumns];

  for (entry = 0;  entry < numEntries;  entry++) {
    explodedata_entry(numLevels, numSizeColumns, 0, levelToColumnIndex2, si, startsi, &di, startdi, sizeColumns, dataSizeColumn, datumBytes, (char*)data, &explodedlen, (char*)exploded);
    printf("\n");
  }

  free(indexes);
  return explodedlen;
}

void plus_lll(ArrayIndex len, int64_t* in1array, int64_t* in2array, int64_t* outarray) {
  ArrayIndex i;
  for (i = 0;  i < len;  i++)
    outarray[i] = in1array[i] + in2array[i];
}

void plus_ldd(ArrayIndex len, int64_t* in1array, double* in2array, double* outarray) {
  ArrayIndex i;
  for (i = 0;  i < len;  i++)
    outarray[i] = in1array[i] + in2array[i];
}

void plus_dld(ArrayIndex len, double* in1array, int64_t* in2array, double* outarray) {
  ArrayIndex i;
  for (i = 0;  i < len;  i++)
    outarray[i] = in1array[i] + in2array[i];
}

void plus_ddd(ArrayIndex len, double* in1array, double* in2array, double* outarray) {
  ArrayIndex i;
  for (i = 0;  i < len;  i++)
    outarray[i] = in1array[i] + in2array[i];
}

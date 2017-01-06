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

#ifndef FEMTOCODE_RUN
#define FEMTOCODE_RUN

#include <inttypes.h>

typedef uint64_t EntryCount;
typedef uint64_t ItemCount;
typedef uint64_t ArrayIndex;
typedef uint32_t LevelIndex;
typedef uint32_t ColumnIndex;
typedef uint32_t NumBytes;

ArrayIndex explodesize(EntryCount numEntries,
                       LevelIndex numLevels,
                       ColumnIndex numSizeColumns,
                       ColumnIndex* levelToColumnIndex,
                       ItemCount** sizeColumns,
                       ItemCount* exploded);

ArrayIndex explodedata(EntryCount numEntries,
                       LevelIndex numLevels,
                       ColumnIndex numSizeColumns,
                       ColumnIndex* levelToColumnIndex,
                       ItemCount** sizeColumns,
                       ColumnIndex dataSizeColumn,
                       NumBytes datumBytes,
                       void* data,
                       void* exploded);

void plus_lll(ArrayIndex len, int64_t* in1array, int64_t* in2array, int64_t* outarray);
void plus_ldd(ArrayIndex len, int64_t* in1array, double* in2array, double* outarray);
void plus_dld(ArrayIndex len, double* in1array, int64_t* in2array, double* outarray);
void plus_ddd(ArrayIndex len, double* in1array, double* in2array, double* outarray);

#endif /* FEMTOCODE_RUN */

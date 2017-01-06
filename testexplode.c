#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

typedef uint64_t EntryCount;
typedef uint64_t ItemCount;
typedef uint64_t ArrayIndex;
typedef uint32_t LevelIndex;
typedef uint32_t ColumnIndex;
typedef uint32_t NumBytes;

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

int main(int argc, char** argv) {
  uint64_t exploded_size;
  uint64_t* exploded = NULL;
  char* exploded_char = NULL;
  float* exploded_float = NULL;
  uint64_t i;

  char trick_data[] = {'a', 'b', 'c'};
  uint64_t trick_size[] = {0, 1, 1, 2, 0, 2};

  char xs2_datac[] = {'a', 'b', 'c', 'd'};
  char xss_datac[] = {'A', 'B', 'C', 'D', 'E', 'F'};
  float xs2_dataf[] = {1.1, 2.2, 3.3, 4.4};
  float xss_dataf[] = {100, 200, 300, 400, 500, 600};
  uint64_t xs2_size[] = {4};
  uint64_t xss_size[] = {3, 2, 2, 2};

  uint32_t levelToColumnIndex1[2];
  uint64_t* sizeColumns1[1];
  uint32_t levelToColumnIndex2[2];
  uint64_t* sizeColumns2[2];
  uint32_t levelToColumnIndex3[3];
  uint64_t* sizeColumns3[2];
  uint32_t levelToColumnIndex4[3];
  uint64_t* sizeColumns4[2];

  printf("trick\n");
  levelToColumnIndex1[0] = 0;
  levelToColumnIndex1[1] = 0;
  sizeColumns1[0] = trick_size;
  exploded_size = explodesize(3, 2, 1, levelToColumnIndex1, sizeColumns1, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explodesize(3, 2, 1, levelToColumnIndex1, sizeColumns1, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(3, 2, 1, levelToColumnIndex1, sizeColumns1, 0, 1, trick_data, NULL);
  exploded_char = malloc(exploded_size * sizeof(char));
  explodedata(3, 2, 1, levelToColumnIndex1, sizeColumns1, 0, 1, trick_data, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n\n");
  free(exploded_char);

  printf("xs2 \\otimes xs2\n");
  levelToColumnIndex2[0] = 0;
  levelToColumnIndex2[1] = 1;
  sizeColumns2[0] = xs2_size;
  sizeColumns2[1] = xs2_size;
  exploded_size = explodesize(1, 2, 2, levelToColumnIndex2, sizeColumns2, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explodesize(1, 2, 2, levelToColumnIndex2, sizeColumns2, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 0, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 0, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 1, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 1, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 0, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 0, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n");
  free(exploded_float);
  exploded_size = explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 1, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levelToColumnIndex2, sizeColumns2, 1, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n\n");
  free(exploded_float);

  printf("xss \\otimes xs2\n");
  levelToColumnIndex3[0] = 0;
  levelToColumnIndex3[1] = 0;
  levelToColumnIndex3[2] = 1;
  sizeColumns3[0] = xss_size;
  sizeColumns3[1] = xs2_size;
  exploded_size = explodesize(1, 3, 2, levelToColumnIndex3, sizeColumns3, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explodesize(1, 3, 2, levelToColumnIndex3, sizeColumns3, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 0, 1, xss_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 0, 1, xss_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 1, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 1, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 0, 4, xss_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 0, 4, xss_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n");
  free(exploded_float);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 1, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex3, sizeColumns3, 1, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n\n");
  free(exploded_float);

  printf("xss[0] \\otimes xs2 \\otimes xss[1]\n");
  levelToColumnIndex4[0] = 0;
  levelToColumnIndex4[1] = 1;
  levelToColumnIndex4[2] = 0;
  sizeColumns4[0] = xss_size;
  sizeColumns4[1] = xs2_size;
  exploded_size = explodesize(1, 3, 2, levelToColumnIndex4, sizeColumns4, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explodesize(1, 3, 2, levelToColumnIndex4, sizeColumns4, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 0, 1, xss_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 0, 1, xss_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 1, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 1, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 0, 4, xss_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 0, 4, xss_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n");
  free(exploded_float);
  exploded_size = explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 1, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levelToColumnIndex4, sizeColumns4, 1, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n\n");
  free(exploded_float);

  return 0;
}

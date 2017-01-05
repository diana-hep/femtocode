#include <stdlib.h>
#include <stdio.h>

void explode_entry(int numLevels, int numSizes, int levi, int* levels, int* si, int* startsi, int** sizes) {
  if (levi == numLevels) {
    printf(".");
  }
  else {
    int level = levels[levi];
    int repeat = sizes[level][si[level]];
    si[level]++;

    for (int j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];

    printf("[");
    for (int i = 0;  i < repeat;  i++) {
      for (int j = 0;  j < numSizes;  j++)
        if (j != level)
          si[j] = startsi[levi * numSizes + j];

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes);
    }
    printf("]");
  }
}

void explode(int numEntries, int numLevels, int numSizes, int* levels, int** sizes) {
  int* si = malloc(numSizes * sizeof(int));
  for (int i = 0;  i < numSizes;  i++) si[i] = 0;

  int* startsi = malloc(numLevels * numSizes * sizeof(int));
  for (int i = 0;  i < numLevels * numSizes;  i++) startsi[i] = 9;
  
  for (int i = 0;  i < numEntries;  i++) {
    explode_entry(numLevels, numSizes, 0, levels, si, startsi, sizes);
    printf("\n");
  }

  free(startsi);
  free(si);
}

int main(int argc, char** argv) {
  /* int trick_size[] = {0, 1, 1, 2, 0, 2}; */
  /* int levels[] = {0, 0}; */
  /* int* sizes[] = {trick_size}; */
  /* explode(3, 2, 1, levels, sizes); */
  /* nonrecursive(3, 2, 1, levels, sizes); */

  /* int xs2_size[] = {4}; */
  /* int levels[] = {0, 1}; */
  /* int* sizes[] = {xs2_size, xs2_size}; */
  /* explode(1, 2, 2, levels, sizes); */

  /* int xss_size[] = {3, 2, 2, 2}; */
  /* int xs2_size[] = {4}; */
  /* int levels[] = {0, 0, 1}; */
  /* int* sizes[] = {xss_size, xs2_size}; */
  /* explode(1, 3, 2, levels, sizes); */

  int xss_size[] = {3, 2, 2, 2};
  int xs2_size[] = {4};
  int levels[] = {0, 1, 0};
  int* sizes[] = {xss_size, xs2_size};
  explode(1, 3, 2, levels, sizes);

  return 0;
}

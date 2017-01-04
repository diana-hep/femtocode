#include <stdlib.h>
#include <stdio.h>

typedef int SIZE;
typedef int LEVEL;

void explode_entry(int numLevels, int levi, LEVEL* levels, int* si, int* startsi, SIZE** sizes) {
  if (levi == numLevels) {
    printf(".");
  }
  else {
    LEVEL level = levels[levi];
    SIZE repeat = sizes[level][si[level]];
    si[level]++;

    for (int j = 0;  j < numLevels;  j++)
      if (levels[j] != levels[levi])
        startsi[levi * numLevels + j] = sizes[levels[j]][si[levels[j]]];
    
    printf("[");
    for (int i = 0;  i < repeat;  i++) {
      for (int j = 0;  j < numLevels;  j++)
        if (levels[j] != levels[levi])
          sizes[levels[j]][si[levels[j]]] = startsi[levi * numLevels + j];

      explode_entry(numLevels, levi + 1, levels, si, startsi, sizes);
    }
    printf("]");
  }
}

void explode(int numEntries, int numLevels, int numSizes, LEVEL* levels, SIZE** sizes) {
  int* si = malloc(numSizes * sizeof(int));
  for (int i = 0;  i < numSizes;  i++) si[i] = 0;

  int* startsi = malloc(numLevels * numLevels * sizeof(int));
  
  for (int i = 0;  i < numEntries;  i++) {
    explode_entry(numLevels, 0, levels, si, startsi, sizes);
    printf("\n");
  }

  free(startsi);
  free(si);
}

int main(int argc, char** argv) {
  /* // char trick_data[] = {'a', 'b', 'c'}; */
  /* SIZE trick_size[] = {0, 1, 1, 2, 0, 2}; */
  /* LEVEL levels[] = {0, 0}; */
  /* SIZE* sizes[] = {trick_size}; */
  /* explode(3, 2, 1, levels, sizes); */

  /* SIZE xs2_size[] = {4}; */
  /* LEVEL levels[] = {0, 1}; */
  /* SIZE* sizes[] = {xs2_size, xs2_size}; */
  /* explode(1, 2, 2, levels, sizes); */

  SIZE xss_size[] = {3, 2, 2, 2};
  SIZE xs2_size[] = {4};
  LEVEL levels[] = {0, 0, 1};
  SIZE* sizes[] = {xss_size, xs2_size};
  explode(1, 3, 2, levels, sizes);

  return 0;
}

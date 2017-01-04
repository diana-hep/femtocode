#include <stdlib.h>
#include <stdio.h>

typedef int SIZE;
typedef int LEVEL;

void explode_entry(int numLevels, LEVEL* levels, int* si, SIZE** sizes) {
  if (numLevels == 0) {
    printf(".");
  }
  else {
    LEVEL l = levels[0];
    SIZE repeat = sizes[l][si[l]];
    si[l]++;

    printf("[");
    for (int i = 0;  i < repeat;  i++) {
      explode_entry(numLevels - 1, &levels[1], si, sizes);
    }
    printf("]");
  }
}

void explode(int numEntries, int numLevels, int numSizes, LEVEL* levels, SIZE** sizes) {
  int* si = malloc(numSizes * sizeof(int));
  for (int i = 0;  i < numSizes;  i++) si[i] = 0;

  for (int i = 0;  i < numEntries;  i++) {
    explode_entry(numLevels, levels, si, sizes);
    printf("\n");
  }

  free(si);
}

int main(int argc, char** argv) {
  // char trick_data[] = {'a', 'b', 'c'};
  SIZE trick_size[] = {0, 1, 1, 2, 0, 2};

  LEVEL levels[] = {0, 0};
  SIZE* sizes[] = {trick_size};
  explode(3, 2, 1, levels, sizes);

  return 0;
}

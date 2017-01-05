#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <sys/time.h>

void explode_entry(uint32_t numLevels, uint32_t numSizes, uint32_t levi, uint32_t* levels, uint32_t* si, uint32_t* startsi, uint32_t** sizes) {
  if (levi == numLevels) {
    printf(".");
  }
  else {
    uint32_t level = levels[levi];
    uint32_t repeat = sizes[level][si[level]];
    si[level]++;

    for (uint32_t j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];

    printf("[");
    for (uint32_t i = 0;  i < repeat;  i++) {
      for (uint32_t j = 0;  j < numSizes;  j++)
        if (j != level)
          si[j] = startsi[levi * numSizes + j];

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes);
    }
    printf("]");
  }
}

void explode(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint32_t** sizes) {
  uint32_t* indexes = malloc((numLevels + numSizes + numLevels * numSizes) * sizeof(uint32_t));

  uint32_t* levels2 = &indexes[0];
  for (uint32_t i = 0;  i < numLevels;  i++) levels2[i] = levels[i];

  uint32_t* si = &indexes[numLevels];
  for (uint32_t i = 0;  i < numSizes;  i++) si[i] = 0;

  uint32_t* startsi = &indexes[numLevels + numSizes];
  
  for (uint64_t i = 0;  i < numEntries;  i++) {
    explode_entry(numLevels, numSizes, 0, levels2, si, startsi, sizes);
    printf("\n");
  }

  free(indexes);
}

int main(int argc, char** argv) {
  /* uint32_t trick_size[] = {0, 1, 1, 2, 0, 2}; */
  /* uint32_t levels[] = {0, 0}; */
  /* uint32_t* sizes[] = {trick_size}; */
  /* explode(3, 2, 1, levels, sizes); */

  /* uint32_t xs2_size[] = {4}; */
  /* uint32_t levels[] = {0, 1}; */
  /* uint32_t* sizes[] = {xs2_size, xs2_size}; */
  /* explode(1, 2, 2, levels, sizes); */

  /* uint32_t xss_size[] = {3, 2, 2, 2}; */
  /* uint32_t xs2_size[] = {4}; */
  /* uint32_t levels[] = {0, 0, 1}; */
  /* uint32_t* sizes[] = {xss_size, xs2_size}; */
  /* explode(1, 3, 2, levels, sizes); */

  uint32_t xss_size[] = {3, 2, 2, 2};
  uint32_t xs2_size[] = {4};
  uint32_t levels[] = {0, 1, 0};
  uint32_t* sizes[] = {xss_size, xs2_size};
  explode(1, 3, 2, levels, sizes);

  return 0;
}

#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

void explode_entry(uint32_t numLevels, uint32_t numSizes, uint32_t levi, uint32_t* levels, uint32_t* si, uint32_t* startsi, uint32_t** sizes) {
  if (levi == numLevels) {
    printf(".");
  }
  else {
    uint32_t coli = levels[levi];
    uint32_t repeat = sizes[coli][si[coli]];
    si[coli]++;

    for (uint32_t j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];

    printf("[");
    for (uint32_t i = 0;  i < repeat;  i++) {
      for (uint32_t j = 0;  j < numSizes;  j++)
        if (j != coli)
          si[j] = startsi[levi * numSizes + j];

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes);
    }
    printf("]");
  }
}

void explode(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint32_t** sizes) {
  uint32_t* indexes = malloc((numLevels + numSizes + numLevels*numSizes) * sizeof(uint32_t));

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
  printf("trick\n");
  uint32_t trick_size[] = {0, 1, 1, 2, 0, 2};
  uint32_t levels1[] = {0, 0};
  uint32_t* sizes1[] = {trick_size};
  explode(3, 2, 1, levels1, sizes1);

  uint32_t xs2_size[] = {4};
  uint32_t xss_size[] = {3, 2, 2, 2};

  printf("xs2 \\otimes xs2\n");
  uint32_t levels2[] = {0, 1};
  uint32_t* sizes2[] = {xs2_size, xs2_size};
  explode(1, 2, 2, levels2, sizes2);

  printf("xss \\otimes xs2\n");
  uint32_t levels3[] = {0, 0, 1};
  uint32_t* sizes3[] = {xss_size, xs2_size};
  explode(1, 3, 2, levels3, sizes3);

  printf("xss[0] \\otimes xs2 \\otimes xss[1]\n");
  uint32_t levels4[] = {0, 1, 0};
  uint32_t* sizes4[] = {xss_size, xs2_size};
  explode(1, 3, 2, levels4, sizes4);

  return 0;
}

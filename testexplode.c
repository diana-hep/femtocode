#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

void explode_entry(uint32_t numLevels, uint32_t numSizes, uint32_t levi, uint32_t* levels, uint64_t* si, uint64_t* startsi, uint64_t** sizes, uint64_t* explodedsize, uint64_t* exploded) {
  if (levi == numLevels) {
    printf(".");
  }
  else {
    uint32_t coli = levels[levi];
    uint64_t repeat = sizes[coli][si[coli]];
    si[coli]++;

    if (exploded != NULL)
      exploded[(*explodedsize)] = repeat;
    (*explodedsize)++;

    for (uint32_t j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];

    printf("[");
    for (uint64_t i = 0;  i < repeat;  i++) {
      for (uint32_t j = 0;  j < numSizes;  j++)
        if (j != coli)
          si[j] = startsi[levi * numSizes + j];

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes, explodedsize, exploded);
    }
    printf("]");
  }
}

// explode takes several 64-bit size arrays and produces a new 64-bit size array (if exploded is not NULL)
// returns the number of 64-bit elements needed for that new size array
uint64_t explode(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint64_t** sizes, uint64_t* exploded) {
  // numEntries is 64-bit because it can index a large number of events
  // si and startsi are 64-bit because they can index a large sizes array
  // everything else is 32-bit because they index a nesting level
  uint32_t* indexes = malloc((numLevels + 2*numSizes + 2*numLevels*numSizes) * sizeof(uint32_t));

  uint32_t* levels2 = &indexes[0];
  for (uint32_t i = 0;  i < numLevels;  i++) levels2[i] = levels[i];

  uint64_t* si = (uint64_t*)&indexes[numLevels];
  for (uint32_t i = 0;  i < numSizes;  i++) si[i] = 0;

  uint64_t* startsi = (uint64_t*)&indexes[numLevels + 2*numSizes];

  uint64_t explodedsize = 0;
  for (uint64_t entry = 0;  entry < numEntries;  entry++) {
    explode_entry(numLevels, numSizes, 0, levels2, si, startsi, sizes, &explodedsize, exploded);
    printf("\n");
  }

  free(indexes);
  return explodedsize;
}

int main(int argc, char** argv) {
  uint64_t exploded_size;
  uint64_t* exploded = NULL;

  printf("trick\n");
  uint64_t trick_size[] = {0, 1, 1, 2, 0, 2};
  uint32_t levels1[] = {0, 0};
  uint64_t* sizes1[] = {trick_size};
  exploded_size = explode(3, 2, 1, levels1, sizes1, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(3, 2, 1, levels1, sizes1, exploded);
  printf("@size = ");
  for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n\n");
  free(exploded);

  uint64_t xs2_size[] = {4};
  uint64_t xss_size[] = {3, 2, 2, 2};

  printf("xs2 \\otimes xs2\n");
  uint32_t levels2[] = {0, 1};
  uint64_t* sizes2[] = {xs2_size, xs2_size};
  exploded_size = explode(1, 2, 2, levels2, sizes2, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(1, 2, 2, levels2, sizes2, exploded);
  printf("@size = ");
  for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n\n");
  free(exploded);

  printf("xss \\otimes xs2\n");
  uint32_t levels3[] = {0, 0, 1};
  uint64_t* sizes3[] = {xss_size, xs2_size};
  exploded_size = explode(1, 3, 2, levels3, sizes3, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(1, 3, 2, levels3, sizes3, exploded);
  printf("@size = ");
  for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n\n");
  free(exploded);

  printf("xss[0] \\otimes xs2 \\otimes xss[1]\n");
  uint32_t levels4[] = {0, 1, 0};
  uint64_t* sizes4[] = {xss_size, xs2_size};
  exploded_size = explode(1, 3, 2, levels4, sizes4, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(1, 3, 2, levels4, sizes4, exploded);
  printf("@size = ");
  for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n\n");
  free(exploded);

  return 0;
}

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

uint64_t explode(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint64_t** sizes, uint64_t* exploded) {
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

void explodedata_entry(uint32_t numLevels, uint32_t numSizes, uint32_t levi, uint32_t* levels, uint64_t* si, uint64_t* startsi, uint64_t* di, uint64_t* startdi, uint64_t** sizes, uint32_t datacolumn, uint32_t datumbytes, char* data, uint64_t* explodedsize, char* exploded) {
  if (levi == numLevels) {
    printf(".");

    if (exploded != NULL) {
      for (uint32_t j = 0;  j < datumbytes;  j++)
        exploded[(*explodedsize) * datumbytes + j] = data[(*di) * datumbytes + j];
    }
    (*explodedsize)++;
    (*di)++;
  }
  else {
    uint32_t coli = levels[levi];
    uint64_t repeat = sizes[coli][si[coli]];
    si[coli]++;

    for (uint32_t j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];
    startdi[levi] = *di;

    printf("[");
    for (uint64_t i = 0;  i < repeat;  i++) {
      for (uint32_t j = 0;  j < numSizes;  j++)
        if (j != coli)
          si[j] = startsi[levi * numSizes + j];

      if (datacolumn != coli)
        *di = startdi[levi];

      explodedata_entry(numLevels, numSizes, levi + 1, levels, si, startsi, di, startdi, sizes, datacolumn, datumbytes, data, explodedsize, exploded);
    }
    printf("]");
  }
}

uint64_t explodedata(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint64_t** sizes, uint32_t datacolumn, uint32_t datumbytes, void* data, void* exploded) {
  uint32_t* indexes = malloc((numLevels + 2*numSizes + 2*numLevels*numSizes + 2*numLevels) * sizeof(uint32_t));

  uint32_t* levels2 = &indexes[0];
  for (uint32_t i = 0;  i < numLevels;  i++) levels2[i] = levels[i];

  uint64_t* si = (uint64_t*)&indexes[numLevels];
  for (uint32_t i = 0;  i < numSizes;  i++) si[i] = 0;

  uint64_t* startsi = (uint64_t*)&indexes[numLevels + 2*numSizes];

  uint64_t di = 0;

  uint64_t* startdi = (uint64_t*)&indexes[numLevels + 2*numSizes + 2*numLevels*numSizes];

  uint64_t explodedsize = 0;
  for (uint64_t entry = 0;  entry < numEntries;  entry++) {
    explodedata_entry(numLevels, numSizes, 0, levels2, si, startsi, &di, startdi, sizes, datacolumn, datumbytes, (char*)data, &explodedsize, (char*)exploded);
    printf("\n");
  }

  free(indexes);
  return explodedsize;
}

int main(int argc, char** argv) {
  uint64_t exploded_size;
  uint64_t* exploded = NULL;
  char* exploded_char = NULL;

  printf("trick\n");
  char trick_data[] = {'a', 'b', 'c'};
  uint64_t trick_size[] = {0, 1, 1, 2, 0, 2};
  uint32_t levels1[] = {0, 0};
  uint64_t* sizes1[] = {trick_size};
  exploded_size = explode(3, 2, 1, levels1, sizes1, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(3, 2, 1, levels1, sizes1, exploded);
  printf("@size = ");
  for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(3, 2, 1, levels1, sizes1, 0, 1, trick_data, NULL);
  exploded_char = malloc(exploded_size * sizeof(char));
  explodedata(3, 2, 1, levels1, sizes1, 0, 1, trick_data, exploded_char);
  printf("@data = ");
  for (uint64_t i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n\n");
  free(exploded_char);

  /* uint64_t xs2_size[] = {4}; */
  /* uint64_t xss_size[] = {3, 2, 2, 2}; */

  /* printf("xs2 \\otimes xs2\n"); */
  /* uint32_t levels2[] = {0, 1}; */
  /* uint64_t* sizes2[] = {xs2_size, xs2_size}; */
  /* exploded_size = explode(1, 2, 2, levels2, sizes2, NULL); */
  /* exploded = malloc(exploded_size * sizeof(uint64_t)); */
  /* explode(1, 2, 2, levels2, sizes2, exploded); */
  /* printf("@size = "); */
  /* for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]); */
  /* printf("\n"); */
  /* free(exploded); */
  /* exploded_size = explodedata(1, 2, 2, levels2, sizes2, 0, 8, NULL, NULL); */
  /* exploded = malloc(exploded_size * sizeof(uint64_t)); */
  /* explodedata(1, 2, 2, levels2, sizes2, 0, 8, NULL, exploded); */
  /* printf("@data = "); */
  /* for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]); */
  /* printf("\n\n"); */
  /* free(exploded); */

  /* printf("xss \\otimes xs2\n"); */
  /* uint32_t levels3[] = {0, 0, 1}; */
  /* uint64_t* sizes3[] = {xss_size, xs2_size}; */
  /* exploded_size = explode(1, 3, 2, levels3, sizes3, NULL); */
  /* exploded = malloc(exploded_size * sizeof(uint64_t)); */
  /* explode(1, 3, 2, levels3, sizes3, exploded); */
  /* printf("@size = "); */
  /* for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]); */
  /* printf("\n"); */
  /* free(exploded); */
  /* exploded_size = explodedata(1, 3, 2, levels3, sizes3, 0, 8, NULL, NULL); */
  /* exploded = malloc(exploded_size * sizeof(uint64_t)); */
  /* explodedata(1, 3, 2, levels3, sizes3, 0, 8, NULL, exploded); */
  /* printf("@data = "); */
  /* for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]); */
  /* printf("\n\n"); */
  /* free(exploded); */

  /* printf("xss[0] \\otimes xs2 \\otimes xss[1]\n"); */
  /* uint32_t levels4[] = {0, 1, 0}; */
  /* uint64_t* sizes4[] = {xss_size, xs2_size}; */
  /* exploded_size = explode(1, 3, 2, levels4, sizes4, NULL); */
  /* exploded = malloc(exploded_size * sizeof(uint64_t)); */
  /* explode(1, 3, 2, levels4, sizes4, exploded); */
  /* printf("@size = "); */
  /* for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]); */
  /* printf("\n"); */
  /* free(exploded); */
  /* exploded_size = explodedata(1, 3, 2, levels4, sizes4, 0, 8, NULL, NULL); */
  /* exploded = malloc(exploded_size * sizeof(uint64_t)); */
  /* explodedata(1, 3, 2, levels4, sizes4, 0, 8, NULL, exploded); */
  /* printf("@data = "); */
  /* for (uint64_t i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]); */
  /* printf("\n\n"); */
  /* free(exploded); */

  return 0;
}

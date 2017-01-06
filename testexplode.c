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
    uint64_t i;
    uint32_t j;
    si[coli]++;

    if (exploded != NULL)
      exploded[(*explodedsize)] = repeat;
    (*explodedsize)++;

    for (j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];

    printf("[");
    for (i = 0;  i < repeat;  i++) {
      for (j = 0;  j < numSizes;  j++)
        if (j != coli)
          si[j] = startsi[levi * numSizes + j];

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes, explodedsize, exploded);
    }
    printf("]");
  }
}

uint64_t explode(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint64_t** sizes, uint64_t* exploded) {
  uint32_t* indexes = malloc((numLevels + 2*numSizes + 2*numLevels*numSizes) * sizeof(uint32_t));
  uint32_t* levels2;
  uint64_t* si;
  uint64_t* startsi;
  uint32_t i;
  uint64_t explodedsize = 0;
  uint64_t entry;

  levels2 = &indexes[0];
  for (i = 0;  i < numLevels;  i++) levels2[i] = levels[i];

  si = (uint64_t*)&indexes[numLevels];
  for (i = 0;  i < numSizes;  i++) si[i] = 0;

  startsi = (uint64_t*)&indexes[numLevels + 2*numSizes];

  for (entry = 0;  entry < numEntries;  entry++) {
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
      uint32_t j;
      for (j = 0;  j < datumbytes;  j++)
        exploded[(*explodedsize) * datumbytes + j] = data[(*di) * datumbytes + j];
    }
    (*explodedsize)++;
    (*di)++;
  }
  else {
    uint32_t coli = levels[levi];
    uint64_t repeat = sizes[coli][si[coli]];
    uint64_t i;
    uint32_t j;
    si[coli]++;

    for (j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];
    startdi[levi] = *di;

    printf("[");
    for (i = 0;  i < repeat;  i++) {
      for (j = 0;  j < numSizes;  j++)
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
  uint64_t* si;
  uint64_t* startsi;
  uint32_t i;
  uint64_t di = 0;
  uint64_t* startdi;
  uint64_t explodedsize = 0;
  uint64_t entry;

  for (i = 0;  i < numLevels;  i++) levels2[i] = levels[i];

  si = (uint64_t*)&indexes[numLevels];
  for (i = 0;  i < numSizes;  i++) si[i] = 0;

  startsi = (uint64_t*)&indexes[numLevels + 2*numSizes];
  startdi = (uint64_t*)&indexes[numLevels + 2*numSizes + 2*numLevels*numSizes];

  for (entry = 0;  entry < numEntries;  entry++) {
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

  uint32_t levels1[2];
  uint64_t* sizes1[1];
  uint32_t levels2[2];
  uint64_t* sizes2[2];
  uint32_t levels3[3];
  uint64_t* sizes3[2];
  uint32_t levels4[3];
  uint64_t* sizes4[2];

  printf("trick\n");
  levels1[0] = 0;
  levels1[1] = 0;
  sizes1[0] = trick_size;
  exploded_size = explode(3, 2, 1, levels1, sizes1, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(3, 2, 1, levels1, sizes1, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(3, 2, 1, levels1, sizes1, 0, 1, trick_data, NULL);
  exploded_char = malloc(exploded_size * sizeof(char));
  explodedata(3, 2, 1, levels1, sizes1, 0, 1, trick_data, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n\n");
  free(exploded_char);

  printf("xs2 \\otimes xs2\n");
  levels2[0] = 0;
  levels2[1] = 1;
  sizes2[0] = xs2_size;
  sizes2[1] = xs2_size;
  exploded_size = explode(1, 2, 2, levels2, sizes2, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(1, 2, 2, levels2, sizes2, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(1, 2, 2, levels2, sizes2, 0, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levels2, sizes2, 0, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 2, 2, levels2, sizes2, 1, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levels2, sizes2, 1, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 2, 2, levels2, sizes2, 0, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levels2, sizes2, 0, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n");
  free(exploded_float);
  exploded_size = explodedata(1, 2, 2, levels2, sizes2, 1, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 2, 2, levels2, sizes2, 1, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n\n");
  free(exploded_float);

  printf("xss \\otimes xs2\n");
  levels3[0] = 0;
  levels3[1] = 0;
  levels3[2] = 1;
  sizes3[0] = xss_size;
  sizes3[1] = xs2_size;
  exploded_size = explode(1, 3, 2, levels3, sizes3, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(1, 3, 2, levels3, sizes3, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(1, 3, 2, levels3, sizes3, 0, 1, xss_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels3, sizes3, 0, 1, xss_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levels3, sizes3, 1, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels3, sizes3, 1, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levels3, sizes3, 0, 4, xss_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels3, sizes3, 0, 4, xss_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n");
  free(exploded_float);
  exploded_size = explodedata(1, 3, 2, levels3, sizes3, 1, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels3, sizes3, 1, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n\n");
  free(exploded_float);

  printf("xss[0] \\otimes xs2 \\otimes xss[1]\n");
  levels4[0] = 0;
  levels4[1] = 1;
  levels4[2] = 0;
  sizes4[0] = xss_size;
  sizes4[1] = xs2_size;
  exploded_size = explode(1, 3, 2, levels4, sizes4, NULL);
  exploded = malloc(exploded_size * sizeof(uint64_t));
  explode(1, 3, 2, levels4, sizes4, exploded);
  printf("@size = ");
  for (i = 0;  i < exploded_size;  i++) printf("%ld ", exploded[i]);
  printf("\n");
  free(exploded);
  exploded_size = explodedata(1, 3, 2, levels4, sizes4, 0, 1, xss_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels4, sizes4, 0, 1, xss_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levels4, sizes4, 1, 1, xs2_datac, NULL);
  exploded_char = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels4, sizes4, 1, 1, xs2_datac, exploded_char);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%c ", exploded_char[i]);
  printf("\n");
  free(exploded_char);
  exploded_size = explodedata(1, 3, 2, levels4, sizes4, 0, 4, xss_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels4, sizes4, 0, 4, xss_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n");
  free(exploded_float);
  exploded_size = explodedata(1, 3, 2, levels4, sizes4, 1, 4, xs2_dataf, NULL);
  exploded_float = malloc(exploded_size * sizeof(uint64_t));
  explodedata(1, 3, 2, levels4, sizes4, 1, 4, xs2_dataf, exploded_float);
  printf("@data(%ld) = ", exploded_size);
  for (i = 0;  i < exploded_size;  i++) printf("%g ", exploded_float[i]);
  printf("\n\n");
  free(exploded_float);

  return 0;
}

#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <sys/time.h>

void explode_entry(uint32_t numLevels, uint32_t numSizes, uint32_t levi, uint32_t* levels, uint32_t* si, uint32_t* startsi, uint32_t** sizes) {
  if (levi == numLevels) {
    // printf(".");
  }
  else {
    uint32_t level = levels[levi];
    uint32_t repeat = sizes[level][si[level]];
    si[level]++;

    for (uint32_t j = 0;  j < numSizes;  j++)
      startsi[levi * numSizes + j] = si[j];

    // printf("[");
    for (uint32_t i = 0;  i < repeat;  i++) {
      for (uint32_t j = 0;  j < numSizes;  j++)
        if (j != level)
          si[j] = startsi[levi * numSizes + j];

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes);
    }
    // printf("]");
  }
}

void explode(uint64_t numEntries, uint32_t numLevels, uint32_t numSizes, uint32_t* levels, uint32_t** sizes) {
  uint32_t* si = malloc(numSizes * sizeof(uint32_t));
  for (uint32_t i = 0;  i < numSizes;  i++) si[i] = 0;

  uint32_t* startsi = malloc(numLevels * numSizes * sizeof(uint32_t));
  for (uint32_t i = 0;  i < numLevels * numSizes;  i++) startsi[i] = 9;
  
  for (uint64_t i = 0;  i < numEntries;  i++) {
    explode_entry(numLevels, numSizes, 0, levels, si, startsi, sizes);
    // printf("\n");
  }

  free(startsi);
  free(si);
}

double time_diff(struct timeval x , struct timeval y) {
    double x_ms , y_ms , diff;
     
    x_ms = (double)x.tv_sec*1000000 + (double)x.tv_usec;
    y_ms = (double)y.tv_sec*1000000 + (double)y.tv_usec;
     
    diff = ((double)y_ms - (double)x_ms) / 1e6;
     
    return diff;
}

int main(int argc, char** argv) {
  /* uint32_t trick_size[] = {0, 1, 1, 2, 0, 2}; */
  /* uint32_t levels[] = {0, 0}; */
  /* uint32_t* sizes[] = {trick_size}; */
  /* explode(3, 2, 1, levels, sizes); */


  uint32_t* trick_size = malloc(30000000 * sizeof(uint32_t));
  for (uint32_t i = 0;  i < 1000000;  i++) {
    trick_size[30*i + 0] = 5;
    trick_size[30*i + 1] = 0;
    trick_size[30*i + 2] = 1;
    trick_size[30*i + 3] = 1;
    trick_size[30*i + 4] = 1;
    trick_size[30*i + 5] = 1;
    trick_size[30*i + 6] = 2;
    trick_size[30*i + 7] = 0;
    trick_size[30*i + 8] = 2;
    trick_size[30*i + 9] = 0;
    trick_size[30*i + 10] = 2;
    trick_size[30*i + 11] = 0;
    trick_size[30*i + 12] = 1;
    trick_size[30*i + 13] = 2;
    trick_size[30*i + 14] = 2;
    trick_size[30*i + 15] = 2;
    trick_size[30*i + 16] = 3;
    trick_size[30*i + 17] = 0;
    trick_size[30*i + 18] = 0;
    trick_size[30*i + 19] = 0;
    trick_size[30*i + 20] = 2;
    trick_size[30*i + 21] = 2;
    trick_size[30*i + 22] = 2;
    trick_size[30*i + 23] = 3;
    trick_size[30*i + 24] = 1;
    trick_size[30*i + 25] = 0;
    trick_size[30*i + 26] = 1;
    trick_size[30*i + 27] = 2;
    trick_size[30*i + 28] = 3;
    trick_size[30*i + 29] = 1;
  }
  uint32_t levels[] = {0, 0, 0, 0, 0};
  uint32_t* sizes[] = {trick_size};

  struct timeval startTime;
  struct timeval endTime;
  double diff;

  gettimeofday(&startTime, NULL);
  explode(1000000, 5, 1, levels, sizes);
  gettimeofday(&endTime, NULL);
  diff = time_diff(startTime, endTime);
  printf("explode %g\n", diff);

  free(trick_size);



  /* uint32_t xs2_size[] = {4}; */
  /* uint32_t levels[] = {0, 1}; */
  /* uint32_t* sizes[] = {xs2_size, xs2_size}; */
  /* explode(1, 2, 2, levels, sizes); */

  /* uint32_t xss_size[] = {3, 2, 2, 2}; */
  /* uint32_t xs2_size[] = {4}; */
  /* uint32_t levels[] = {0, 0, 1}; */
  /* uint32_t* sizes[] = {xss_size, xs2_size}; */
  /* explode(1, 3, 2, levels, sizes); */

  /* uint32_t xss_size[] = {3, 2, 2, 2}; */
  /* uint32_t xs2_size[] = {4}; */
  /* uint32_t levels[] = {0, 1, 0}; */
  /* uint32_t* sizes[] = {xss_size, xs2_size}; */
  /* explode(1, 3, 2, levels, sizes); */

  return 0;
}

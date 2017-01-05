#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>

typedef int SIZE;
typedef int LEVEL;

void nonrecursive(int numEntries, int numLevels, int numSizes, LEVEL* levels, SIZE** sizes) {
  int* countdown = malloc((numLevels + 1) * numSizes * sizeof(int));
  int* deepi = malloc(numSizes * sizeof(int));
  int* datai = malloc(numSizes * sizeof(int));
  int* sizei = malloc(numSizes * sizeof(int));

  for (int i = 0;  i < numSizes;  i++) {
    deepi[i] = 0;
    datai[i] = 0;
    sizei[i] = 0;
  }

  int coli = 0;
  int levi = 0;
  int entry = 0;
  while (entry < numEntries) {
    if (levi < numLevels)
      coli = levels[levi];

    if (deepi[coli] != 0)
      countdown[coli * numSizes + deepi[coli]]--;

    if (deepi[coli] == numLevels) {
      // printf(".");
      datai[coli]++;
    }
    else {
      levi++;
      deepi[coli]++;
      countdown[coli * numSizes + deepi[coli]] = sizes[coli][sizei[coli]];
      sizei[coli]++;
      // printf("[");
    }

    while (deepi[coli] != 0  &&  countdown[coli * numSizes + deepi[coli]] == 0) {
      levi--;
      deepi[coli]--;
      // printf("]");
    }

    if (levi == 0) {
      entry++;
      // printf("\n");
    }
  }

  free(sizei);
  free(datai);
  free(deepi);
  free(countdown);
}

void explode_entry(int numLevels, int numSizes, int levi, LEVEL* levels, int* si, int* startsi, SIZE** sizes) {
  if (levi == numLevels) {
    // printf(".");
  }
  else {
    LEVEL level = levels[levi];
    SIZE repeat = sizes[level][si[level]];
    si[level]++;

    /* for (int j = 0;  j < numSizes;  j++) */
    /*   startsi[levi * numSizes + j] = si[j]; */

    // printf("[");
    for (int i = 0;  i < repeat;  i++) {
      /* for (int j = 0;  j < numSizes;  j++) */
      /*   if (j != level) */
      /*     si[j] = startsi[levi * numSizes + j]; */

      explode_entry(numLevels, numSizes, levi + 1, levels, si, startsi, sizes);
    }
    // printf("]");
  }
}

void explode(int numEntries, int numLevels, int numSizes, LEVEL* levels, SIZE** sizes) {
  int* si = malloc(numSizes * sizeof(int));
  for (int i = 0;  i < numSizes;  i++) si[i] = 0;

  int* startsi = malloc(numLevels * numSizes * sizeof(int));
  for (int i = 0;  i < numLevels * numSizes;  i++) startsi[i] = 9;
  
  for (int i = 0;  i < numEntries;  i++) {
    explode_entry(numLevels, numSizes, 0, levels, si, startsi, sizes);
    // printf("\n");
  }

  free(startsi);
  free(si);
}

double time_diff(struct timeval x , struct timeval y)
{
    double x_ms , y_ms , diff;
     
    x_ms = (double)x.tv_sec*1000000 + (double)x.tv_usec;
    y_ms = (double)y.tv_sec*1000000 + (double)y.tv_usec;
     
    diff = ((double)y_ms - (double)x_ms) / 1e6;
     
    return diff;
}

int main(int argc, char** argv) {
  /* SIZE trick_size[] = {0, 1, 1, 2, 0, 2}; */
  /* LEVEL levels[] = {0, 0}; */
  /* SIZE* sizes[] = {trick_size}; */
  /* explode(3, 2, 1, levels, sizes); */
  /* nonrecursive(3, 2, 1, levels, sizes); */


  SIZE* trick_size = malloc(30000000 * sizeof(SIZE));
  for (int i = 0;  i < 1000000;  i++) {
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
  LEVEL levels[] = {0, 0, 0, 0, 0};
  SIZE* sizes[] = {trick_size};

  struct timeval startTime;
  struct timeval endTime;
  double diff;

  gettimeofday(&startTime, NULL);
  explode(1000000, 5, 1, levels, sizes);
  gettimeofday(&endTime, NULL);
  diff = time_diff(startTime, endTime);
  printf("explode %g\n", diff);

  gettimeofday(&startTime, NULL);
  nonrecursive(1000000, 5, 1, levels, sizes);
  gettimeofday(&endTime, NULL);
  diff = time_diff(startTime, endTime);

  printf("nonrecursive %g\n", diff);

  free(trick_size);



  /* SIZE xs2_size[] = {4}; */
  /* LEVEL levels[] = {0, 1}; */
  /* SIZE* sizes[] = {xs2_size, xs2_size}; */
  /* explode(1, 2, 2, levels, sizes); */

  /* SIZE xss_size[] = {3, 2, 2, 2}; */
  /* SIZE xs2_size[] = {4}; */
  /* LEVEL levels[] = {0, 0, 1}; */
  /* SIZE* sizes[] = {xss_size, xs2_size}; */
  /* explode(1, 3, 2, levels, sizes); */

  /* SIZE xss_size[] = {3, 2, 2, 2}; */
  /* SIZE xs2_size[] = {4}; */
  /* LEVEL levels[] = {0, 1, 0}; */
  /* SIZE* sizes[] = {xss_size, xs2_size}; */
  /* explode(1, 3, 2, levels, sizes); */

  return 0;
}

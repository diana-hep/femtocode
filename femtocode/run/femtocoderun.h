// Copyright 2016 DIANA-HEP
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <stdint.h>

template <typename IN1, typename IN2, typename OUT>
void plus_flatflat(int64_t len, IN1* in1array, IN2* in2array, OUT* outarray) {
  for (int64_t i = 0;  i < len;  i++)
    outarray[i] = in1array[i] + in2array[i];
}

// template <typename IN1, typename IN2, typename OUT>
// void plus_sizeflat(int64_t size1len, int64_t* size1array,
//                    int64_t in1len, IN1* in1array,
//                    int64_t in2len, IN1* in2array,
//                    OUT* outarray) {
  



//   for (int64_t i = 0;  i < len;  i++)
//     outarray[i] = in1array[i] + in2array[i];
// }

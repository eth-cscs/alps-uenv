# HIP programming environments for AMD GPUs

* Need to build the stack on an compute node with an AMD GPU, otherwise HIP can't be built
* CMake `enable_language(HIP)` might not work with the generated modules, use the generated view instead
* CMake version: newer than 3.24.4 is possible, but might require `-DCMAKE_HIP_COMPILER=$(which amdclang++) -DCMAKE_HIP_COMPILER_FORCED=ON`
  for HIP to work

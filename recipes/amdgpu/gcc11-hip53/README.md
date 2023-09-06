# GCC 11 with HIP 5.3 and HDF5

## Limitations

* Need to build stack on an compute node with AMD GPUs, otherwise HIP can't be built
* CMake `enable_language(HIP)` might not work with the generated modules, use the generated view instead

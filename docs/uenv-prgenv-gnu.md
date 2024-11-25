# prgenv-gnu uenv

Provides a small set of tools and libraries built around the GNU compiler toolchain.

It provides the GCC compilers (gcc, g++ and gfortran), MPI (cray-mpich), Python, cuda (on systems with NVIDIA GPUs).

The following packages are provided:
  
* `aws-ofi-nccl`
* `boost`
* `cmake`
* `cray-mpich`
    * built with `cuda` support on systems with NVIDIA GPUs
* `cuda`
    * only on systems with NVIDIA GPUs
* `fftw`
* `fmt`
* `gcc`
* `gsl`
* `hdf5`
* `kokkos`
* `kokkos-kernels`
* `kokkos-tools`
* `libtree`
* `meson`
* `nccl-tests`
* `nccl`
* `ninja`
* `openblas`
    * built with OpenMP support
* `osu-micro-benchmarks`
* `python`
    * a recent version of python 3

## Changelog

### 24.11

- Added GSL
- Added Boost with Chrono, Filesystem, Iostreams, MPI, Python, Regex, Serialization, System, Timer
- Added Kokkos with the CUDA, OpenMP, and Serial execution spaces
- Added Kokkos Kernels with explicit template instantiations and support for the most commonly used third party libraries
- Added Kokkos Tools
- Added PAPI
- Added SuperLU
- Added netlib-scalapack
- Added Lua
- Added lz4
- Added zlib-ng
- Added C++ and Fortran support to HDF5
- Updated CUDA to 12.6
- Changed aws-ofi-nccl to 1.9.2

## How to use

The environment is designed as a fairly minimal set of 

There are three ways to access the software provided by prgenv-gnu, once it has been started.

=== "views"

    The simplest way to get started is to use the file system view. A single view is provided:

    * before v24.7: the `default` view
    * since v24.7: the `develop` view

    ```
    # set when starting the uenv
    uenv start --view=develop prgenv-gnu/24.7:v1

    # set after starting
    # NOTE: this method will be deprecated
    uenv start prgenv-gnu/24.7:v1
    uenv view develop

    # example: the python executable provided by the uenv will be available
    which python
    /user-environment/env/default/bin/python

    # example: the python version is more recent that the 3.6 version in /usr/bin
    python --version 
    Python 3.12.1
    ```


=== "modules"

    The uenv provides modules for all of the software packages.
    The modules are not available by default when a uenv starts, and have to be enabled.

    ```bash
    # with v4 of uenv:
    uenv start prgenv-gnu/24.7
    uenv modules use

    # with v5 of uenv:

    # method 1: enable modules when the uenv is started
    uenv start --view=modules prgenv-gnu/24.7

    # method 2: enable modules after the uenv has started
    uenv start prgenv-gnu/24.7
    uenv view modules
    ```

=== "spack"

    To use Spack, you can check the [guide for using Spack with uenv](https://eth-cscs.github.io/alps-uenv/uenv-compilation-spack/).

    !!! note

        If using the most recent release of uenv and a compatible uenv, load the `spack` view:

        ```bash
        # start the uenv with the spack view
        # note: the version might differ from the one in this example
        uenv start --view=spack prgenv-gnu/24.7:v1
        ```

        Loading the `spack` view sets the following environment variables (with example values):

        ```
        UENV_SPACK_CONFIG_PATH  /user-environment/config
        UENV_SPACK_URL          https://github.com/spack/spack.git
        UENV_SPACK_COMMIT       b5fe93fee1eec46a0750bd340198bffcb92ff9eec
        ```

## platform specific hints

=== "gh200"

    The version of MPI (cray-mpich) provided on Grace Hopper systems (Todi at the time of writing) supports GPU-direct or GPU aware communication, whereby pointers to GPU buffers can be passed directly to MPI calls.
    No special steps have to be taken to compile your code, however the following environment variable must be set to run an application that uses GPU pointers:

    ```bash
    export MPICH_GPU_SUPPORT_ENABLED=1
    ```


=== "multicore"

    There are no platform-specific notes for multicore.


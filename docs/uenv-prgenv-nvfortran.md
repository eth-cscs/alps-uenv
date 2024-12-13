# prgenv-nvfortran uenv

Provides a small set of tools and libraries for building applications that need the NVIDIA Fortran compiler:

* applications that use OpenACC for GPU acceleration;
* applications that use CUDA Fortran for GPU acceleration.

It provides the NVHPC compilers, MPI (cray-mpich), Python, cuda

The naming scheme is `prgenv-nvidia/<version>:v<i>`, where `<version>` matches the version of the NVIDIA HPC SDK.

* the SDK is released every two months, and is numbered in the `YY.MM` format, e.g. `24.1` and `24.11`.
* the `prgenv-nvfortran` will be released three times a year (every second NVHPC release).

## Using the uenv

The image is only provided on Alps systems that have NVIDIA GPUs.
To see which versions have been installed on a system, log in then search:

```
# search for uenv
uenv image find prgenv-nvfortran

# pull a version
uenv image find prgenv-nvfortran/24.11:v1
```

To use the uenv, we recommend using the uenv view `--view=nvfort`:

```
uenv start prgenv-nvfortran/24.11:v1 --view=nvfort
mpif90 --version
```

The above example shows that the MPI compiler wrappers are using the underlying NVIDIA compiler.
The following wrappers are available:

* `mpif77`
* `mpif90`
* `mpifort`

And the following C/C++ wrapers are available:

* `mpicc`
* `mpicxx`
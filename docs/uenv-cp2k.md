# CP2K

[CP2K](https://www.cp2k.org/) version `2023.2`.

An environment that provides the latest version of [CP2K](https://www.cp2k.org/), along with the libraries and tools required to build a different or custom version of [CP2K](https://www.cp2k.org/).

The following environment views are provided:

* `cp2k-scalapack`: CP2K, dependencies, and [ScaLAPACK](https://www.netlib.org/scalapack/) as diagonalization library
* `cp2k-scalapack-dev`: dependencies and [ScaLAPACK](https://www.netlib.org/scalapack/)
* `cp2k-elpa`: CP2K, dependencies, and [ELPA](https://elpa.mpcdf.mpg.de/) as diagonalization library
* `cp2k-elpa-dev`: dependencies and [ELPA](https://elpa.mpcdf.mpg.de/)

## Building a custom version of CP2K

### Using modules

To build your version of QE do the following steps:

```bash
# Load the required modules
module load [...]
cd cp2k
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCP2K_SCALAPACK_VENDOR=MKL -DCP2K_USE_ACCEL=cuda -DCP2K_WITH_GPU=A100
make -j20
```

See CP2K's [README_cmake.md](https://github.com/cp2k/cp2k/blob/master/README_cmake.md) for details.

### Using Spack

```bash
uenv start cp2k-a100.squashfs
export SPACK_SYSTEM_CONFIG_PATH=/user-environment/config/
spack install cp2k [...]
```

See Spack's [CP2K package](https://packages.spack.io/package.html?name=cp2k) for details.

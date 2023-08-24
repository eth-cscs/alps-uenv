# Quantum ESPRESSO

https://www.quantum-espresso.org/

An environment that provides the latest version of Quantum ESPRESSO, along with the libraries and tools required to build a different or custom version of Quantum ESPRESSO.
At the moment a GPU-build environment is provided without a ScaLAPACK.

The following environment views are provided:
 * default : QuantumESPRESSO/7.1 itself + dependencies
 * develop : only dependencies

The following modules are provided:
 * cmake/3.26.3
 * cray-mpich/8.1.25-nvhpc
 * cuda/11.8.0
 * fftw/3.3.10
 * gcc/11.3.0
 * libxc/5.2.3-nvhpc
 * nvhpc/22.11
 * openblas/0.3.23
 * patchelf/0.17.2
 * quantum-espresso/7.1


To build your version of QE do the following steps:
 ```
module load cmake cray-mpich/8.1.25-nvhpc cuda fftw libxc/5.2.3-nvhpc nvhpc openblas
cd qe-71-dev
mkdir build && cd build
cmake .. -DQE_ENABLE_OPENMP=1 -DQE_ENABLE_SCALAPACK=0 -DQE_ENABLE_LIBXC=1 -DQE_ENABLE_CUDA=1
make -j20
```

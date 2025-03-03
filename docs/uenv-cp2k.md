# CP2K

[CP2K] is a quantum chemistry and solid state physics software package that can perform atomistic simulations of solid state, liquid, molecular, periodic, material, crystal, and biological systems.

CP2K provides a general framework for different modeling methods such as DFT using the mixed Gaussian and plane waves approaches GPW and GAPW. Supported theory levels include DFTB, LDA, GGA, MP2, RPA, semi-empirical methods (AM1, PM3, PM6, RM1, MNDO, …), and classical force fields (AMBER, CHARMM, …). CP2K can do simulations of molecular dynamics, metadynamics, Monte Carlo, Ehrenfest dynamics, vibrational analysis, core level spectroscopy, energy minimization, and transition state optimization using NEB or dimer method. See [CP2K Features] for a detailed overview.

## Running

```bash
uenv start -view=modules <CP2K_UENV>
module load cp2k
```

or

```bash
uenv start --view=cp2k <CP2K_UENV>
```

!!! warning
    [COSMA] is built with GPU-aware MPI. Make sure to set `MPICH_GPU_SUPPORT_ENABLED=1` when running [CP2K].

!!! warning
    [DLA-Future] is built with GPU-aware MPI. Make sure to set `MPICH_GPU_SUPPORT_ENABLED=1` when running [CP2K].

## Building from source

The [CP2K] `uenv` provides all the dependencies required to build [CP2K] from source, with several optional features enabled. You can follow these steps to build [CP2K] from source:

```bash
# Start uenv and load develop view
uenv start --view=develop <CP2K_UENV>

# cd to CP2K source directory
cd <PATH_TO_CP2K_SOURCE>

# CMake
mkdir build && cd build
CC=mpicc CXX=mpic++ FC=mpifort cmake \
    -GNinja \
    -DCMAKE_CUDA_HOST_COMPILER=mpicc \
    -DCP2K_USE_LIBXC=ON \
    -DCP2K_USE_LIBINT2=ON \
    -DCP2K_USE_SPGLIB=ON \
    -DCP2K_USE_ELPA=ON \
    -DCP2K_USE_SPLA=ON \
    -DCP2K_USE_SIRIUS=ON \
    -DCP2K_USE_COSMA=ON \
    -DCP2K_USE_PLUMED=ON \
    -DCP2K_USE_DFTD4=ON \
    -DCP2K_USE_DLAF=ON \
    -DCP2K_USE_ACCEL=CUDA -DCP2K_WITH_GPU=H100 \
    ..

ninja -j 32
```

!!! note

    `cp2k@2024.1` and earlier does not support compiling for `cuda_arch=90`. Use `-DCP2K_WITH_GPU=A100` instead.

!!! note

    On `x86` we deploy with `intel-oneapi-mkl` and `libxsmm` before `cp2k@2025.1`.
    If you are using a pre-`cp2k@2025.1` UENV, add `-DCP2K_SCALAPACK_VENDOR=MKL` to the CMake invocation to find MKL.

!!! note

    On `x86` we deploy with `libxmm`. Add `-DCP2K_USE_LIBXSMM=ON` to use `libxsmm`.

See [manual.cp2k.org/CMake] for more details.

[CP2K]: https://www.cp2k.org/
[CP2K Features]: https://www.cp2k.org/features
[COSMA]: https://github.com/eth-cscs/COSMA
[DLA-Future]: https://github.com/eth-cscs/DLA-Future
[manual.cp2k.org/CMake]: https://manual.cp2k.org/trunk/getting-started/CMake.html

# CP2K

Spack stack for [CP2K](https://www.cp2k.org/).

> CP2K is a quantum chemistry and solid state physics software package that can perform atomistic simulations of solid state, liquid, molecular, periodic, material, crystal, and biological systems. CP2K provides a general framework for different modeling methods such as DFT using the mixed Gaussian and plane waves approaches GPW and GAPW. Supported theory levels include DFTB, LDA, GGA, MP2, RPA, semi-empirical methods (AM1, PM3, PM6, RM1, MNDO, …), and classical force fields (AMBER, CHARMM, …). CP2K can do simulations of molecular dynamics, metadynamics, Monte Carlo, Ehrenfest dynamics, vibrational analysis, core level spectroscopy, energy minimization, and transition state optimization using NEB or dimer method.

Provided versions:
* [`2024.1`](https://github.com/cp2k/cp2k/releases/tag/v2024.1)

## Usage

CP2K is built with [DLA-Future](https://github.com/eth-cscs/DLA-Future), [ELPA](https://elpa.mpcdf.mpg.de/), and ScaLAPACK support for the solution of eigenvalue problems. You can use the [`PREFERRED_DIAG_LIBRARY`](https://manual.cp2k.org/trunk/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PREFERRED_DIAG_LIBRARY) keyword in the CP2K input file to select the preferred diagonalisation library:

```
&GLOBAL
    [...]
    PREFERRED_DIAG_LIBRARY DLAF
&END GLOBAL
```

!!! warning
    [COSMA](https://github.com/eth-cscs/COSMA) is built with GPU-aware MPI. Make sure to set `MPICH_GPU_SUPPORT_ENABLED=1` when running CP2K.

## Building a custom version of CP2K

### Using modules

To build your version of CP2K do the following steps:

```bash
# Load the required modules
module load [...]
cd cp2k
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCP2K_SCALAPACK_VENDOR=MKL -DCP2K_USE_ACCEL=CUDA -DCP2K_WITH_GPU=A100
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

# Quantum ESPRESSO

https://www.quantum-espresso.org

An environment that provides the latest version of Quantum ESPRESSO, along with the libraries and tools required to build a different or custom version of Quantum ESPRESSO.
At the moment a GPU-build environment is provided without a ScaLAPACK.

The following environment views are provided:

* default : QuantumESPRESSO/7.3.1 itself + dependencies
* develop : only dependencies

The following modules are provided:

* cmake/3.27.7
* nvhpc/24.1
* quantum-espresso/7.3.1
* cray-mpich/8.1.29
* fftw/3.3.10
* git/2.42.0
* nvpl-lapack/0.2.0
* gcc/12.3.0
* libxc/6.2.2
* nvpl-blas/0.1.0

# Building a custom version

## Using modules

```bash
uenv start quantumespresso/v7.3.1
uenv modules use
module load cmake \
    fftw \
    nvhpc \
    nvpl-lapack \
    nvpl-blas \
    cray-mpich \
    netlib-scalapack \
    libxc

mkdir build && cd build
cmake .. \
    -DQE_ENABLE_MPI=ON \
    -DQE_ENABLE_OPENMP=ON \
    -DQE_ENABLE_SCALAPACK:BOOL=OFF \
    -DQE_ENABLE_LIBXC=ON \
    -DQE_ENABLE_CUDA=ON \
    -DQE_ENABLE_PROFILE_NVTX=ON \
    -DQE_CLOCK_SECONDS:BOOL=OFF \
    -DQE_ENABLE_MPI_GPU_AWARE:BOOL=OFF \
    -DQE_ENABLE_OPENACC=ON
make -j20
```


## Using spack

Clone spack
```bash
uenv start quantumespresso/v7.3.1
# clone the same spack version as has been used to build the uenv
git clone -b $(jq -r .spack.commit /user-environment/meta/configure.json) $(jq -r .spack.repo /user-environment/meta/configure.json) $SCRATCH/spack
```

Activate spack with the uenv configured as upstream
```bash
# ensure spack is using the uenv as upstream repository (always required)
export SPACK_SYSTEM_CONFIG_PATH=/user-environment/config
# active spack (always required)
. $SCRATCH/spack/share/spack/setup-env.sh
```

Create an anonymous environment for QE
```bash
spack env create -d $SCRATCH/qe-env
spack -e $SCRATCH/qe-env add quantum-espresso%nvhpc +cuda
spack -e $SCRATCH/qe-env config add packages:all:prefer:cuda_arch=90
spack -e $SCRATCH/qe-env develop -p /path/to/your/QE-src quantum-espresso@=develop
spack -e $SCRATCH/qe-env concretize -f
```

Check the output of `spack concretize -f`. All dependencies should have been picked up from spack upstream, marked eiter by a green `[^]` or `[e]`.

```bash
spack -e $SCRATCH/qe-env env view enable view
spack -e $SCRATCH/qe-env install
```

To recompile QE after editing the source code re-run `spack -e $SCRATCH/qe-env install`.

Running `pw.x`:
```bash
uenv start quantumespresso/v7.3.1
srun [...] $SCRATCH/qe-env/view/bin/pw.x < pw.in
```






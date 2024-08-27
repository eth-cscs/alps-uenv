# Quantum ESPRESSO

https://www.quantum-espresso.org

An environment that provides the latest version of Quantum ESPRESSO, along with the libraries and tools required to build a different or custom version of Quantum ESPRESSO.
At the moment a GPU-build environment is provided without a ScaLAPACK.

The following environment views are provided:

=== "GH200"

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

=== "A100"

    * default : QuantumESPRESSO/7.1 itself + dependencies
    * develop : only dependencies

    The following modules are provided:

    * cmake/3.26.3
    * cray-mpich/8.1.25-nvhpc
    * cuda/11.8.0
    * fftw/3.3.10
    * gcc/11.3.0
    * libxc/5.2.3
    * nvhpc/22.11
    * openblas/0.3.23
    * patchelf/0.17.2
    * quantum-espresso/7.1


# Building a custom version

## Using modules

=== "GH200"

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
    FC=mpif90 CXX=mpic++ CC=mpicc cmake .. \
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

=== "A100"

    ```bash
    uenv start quantumespresso/v7.1
    uenv modules use
    module load cmake \
        cray-mpich
        cuda \
        fftw \
        gcc \
        libxc \
        nvhpc \
        openblas
    mkdir build && cd build
    FC=mpif90 CXX=mpic++ CC=mpicc cmake .. \
        -DQE_ENABLE_MPI=ON \
        -DQE_ENABLE_OPENMP=ON \
        -DQE_ENABLE_SCALAPACK:BOOL=OFF \
        -DQE_ENABLE_LIBXC=ON \
        -DQE_ENABLE_CUDA=ON \
        -DQE_CLOCK_SECONDS:BOOL=OFF \
        -DQE_ENABLE_MPI_GPU_AWARE:BOOL=OFF \
        -DQE_ENABLE_OPENACC=ON
    make -j20
    ```

## Using spack

1. Clone spack using the same version that has been used to build the uenv. 
```bash
uenv start quantumespresso/v7.3.1
# clone the same spack version as has been used to build the uenv
git clone -b $(jq -r .spack.commit /user-environment/meta/configure.json) $(jq -r .spack.repo /user-environment/meta/configure.json) $SCRATCH/spack
```

2. Activate spack with the uenv configured as upstream
```bash
# ensure spack is using the uenv as upstream repository (always required)
export SPACK_SYSTEM_CONFIG_PATH=/user-environment/config
# active spack (always required)
. $SCRATCH/spack/share/spack/setup-env.sh
```

3. Create an anonymous environment for QE
```bash
spack env create -d $SCRATCH/qe-env
spack -e $SCRATCH/qe-env add quantum-espresso%nvhpc +cuda
spack -e $SCRATCH/qe-env config add packages:all:prefer:cuda_arch=90
spack -e $SCRATCH/qe-env develop -p /path/to/your/QE-src quantum-espresso@=develop
spack -e $SCRATCH/qe-env concretize -f
```
Check the output of `spack concretize -f`. All dependencies should have been picked up from spack upstream, marked eiter by a green `[^]` or `[e]`.
Next we create a local filesystem view, this instructs spack to create symlinks for binaries and libraries in a local directory `view`.
```bash
spack -e $SCRATCH/qe-env env view enable view
spack -e $SCRATCH/qe-env install
```
To recompile QE after editing the source code re-run `spack -e $SCRATCH/qe-env install`.

4. Run `pw.x` using the filesystem view generated in 3.
```bash
uenv start quantumespresso/v7.3.1
MPICH_GPU_SUPPORT_ENABLED=1 srun [...] $SCRATCH/qe-env/view/bin/pw.x < pw.in
```
Note: The `pw.x` is linked to the uenv, it won't work without activating the uenv, also it will only work with the exact same version of the uenv. The physical installation path is in `$SCRATCH/spack`, deleting this directory will leave the anonymous spack environment created in 3. with dangling symlinks.






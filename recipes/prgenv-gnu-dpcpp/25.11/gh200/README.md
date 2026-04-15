# prgenv-gnu-dpcpp

> **Status: Experimental**

GNU compiler toolchain with Intel DPC++ SYCL compiler and CUDA backend for
GH200 on Alps aarch64 systems.

## Overview

This recipe extends `prgenv-gnu/25.11` with Intel DPC++ built from source.
The Intel oneAPI binary distribution is x86_64 only, so a custom Spack package
(`llvmdpcpp`) builds the compiler from the
[intel/llvm](https://github.com/intel/llvm) `sycl` branch directly on aarch64.

The environment includes everything from `prgenv-gnu/25.11` (cray-mpich, Boost,
HDF5, NetCDF, Kokkos, FFTW, etc.) plus:

- Intel DPC++ compiler (`clang++ -fsycl`) with CUDA backend targeting sm_90
- GPU-aware MPI (cray-mpich + GTL CUDA) compatible with SYCL device pointers

## Changes from prgenv-gnu/25.11

### config.yaml
- Spack pinned to `v1.1.1` (stable release)
- spack-packages updated to `7178c89` (2026-03-09)
- Added `default-view: default`

### environments.yaml
- `unify: when_possible` (required for DPC++ concretization)
- `cuda@12` pinned
- Added `llvmdpcpp@sycl +clang +cuda cuda_arch=90`

### Custom Spack package: llvmdpcpp
Located at `repo/packages/llvmdpcpp/package.py`. Key details:

- Fetches `https://github.com/intel/llvm.git` branch `sycl`
- CMakeLists.txt is in the `llvm/` subdirectory
- Enables SYCL runtime, llvm-spirv, xpti, xptifw, libdevice, sycl-jit, libclc
- CUDA backend via `SYCL_ENABLE_BACKENDS=opencl;level_zero;cuda`
- `compiler-rt` excluded (system GCC too old for sanitizer code on aarch64)
- XPTI tracing disabled (avoids CUPTI path issues in uenv)
- Uses Spack 1.0+ API (`spack_repo.builtin.build_systems` imports)

## Build

Build on a compute node using `/dev/shm` for performance:

```bash
salloc -N 1 --time=240 -A <ACCOUNT>

mkdir -p /dev/shm/$USER
git clone https://github.com/eth-cscs/stackinator.git /dev/shm/$USER/stackinator
uv tool install --editable /dev/shm/$USER/stackinator
git clone git@github.com:eth-cscs/alps-cluster-config.git /dev/shm/$USER/alps-cluster-config

stack-config \
    --build /dev/shm/$USER/dpc \
    --recipe /path/to/recipes/prgenv-gnu-dpcpp/25.11/gh200 \
    --system /dev/shm/$USER/alps-cluster-config/<cluster>

# Workaround: pre-create CXI staging directories (Spack bug with / in version strings)
mkdir -p /dev/shm/$USER/dpc/tmp/$USER/spack-stage/spack-stage-{cxi-driver,cassini-headers,libcxi}-git.release

cd /dev/shm/$USER/dpc
env --ignore-environment PATH=/usr/bin:/bin:$(pwd -P)/spack/bin HOME=$HOME make store.squashfs -j144

# Copy to persistent storage
cp store.squashfs /path/to/persistent/dpcpp-prgenv.squashfs
```

Build time: ~2-3 hours on a single GH200 node.

## Usage

### Setup

```bash
uenv start --view=default /path/to/dpcpp-prgenv.squashfs
export CUDA_PATH=$(ls -d /user-environment/linux-neoverse_v2/cuda-*)
```

### Compile

```bash
# Non-MPI
clang++ -std=c++17 -O3 -fsycl \
    -fsycl-targets=nvptx64-nvidia-cuda \
    -Xsycl-target-backend --cuda-gpu-arch=sm_90 \
    --cuda-path=$CUDA_PATH \
    source.cpp -o binary

# MPI (MPICH_CXX tells mpicxx to use DPC++ instead of g++)
MPICH_CXX=clang++ mpicxx -std=c++17 -O3 -fsycl \
    -fsycl-targets=nvptx64-nvidia-cuda \
    -Xsycl-target-backend --cuda-gpu-arch=sm_90 \
    --cuda-path=$CUDA_PATH \
    source.cpp -o binary
```

### Run

```bash
# Single GPU
srun -n 1 -A <ACCOUNT> \
    --uenv=/path/to/dpcpp-prgenv.squashfs \
    /path/to/bind_numa.sh ./binary

# Multi-node MPI
srun -n 8 -N 2 -A <ACCOUNT> --mpi=cray_shasta \
    --uenv=/path/to/dpcpp-prgenv.squashfs \
    --export=ALL,MPICH_GPU_SUPPORT_ENABLED=1 \
    /path/to/bind_numa.sh ./binary
```

### GPU-aware MPI

SYCL device pointers (`sycl::malloc_device`) can be passed directly to MPI
calls without host staging. Requires `MPICH_GPU_SUPPORT_ENABLED=1`, which can
be set via `--export` on the `srun` command line or in the `bind_numa.sh`
wrapper script.

### oneAPI DPL

If the application uses `#include <oneapi/dpl/...>` headers, oneDPL must be
provided separately (it is not included in the uenv):

```bash
git clone https://github.com/oneapi-src/oneDPL.git /path/to/oneDPL
# Add to compile command: -I/path/to/oneDPL/include
```

## Known issues

1. **CXI staging directories**: Spack has a bug with `/` in version strings
   for CXI network packages (`cxi-driver`, `cassini-headers`, `libcxi`).
   Staging directories must be pre-created before building (see build
   instructions above).

2. **UR/CUDA cleanup errors at exit**: The DPC++ runtime may report
   `UR_RESULT_ERROR_UNKNOWN` errors during program exit. These are caused by
   SYCL device memory not being explicitly freed before `MPI_Finalize()` and
   do not affect simulation results.

3. **`--mpi=cray_shasta`**: Required on Clariden for MPI to initialize
   correctly. Not required on Santis.

4. **`--cuda-path`**: Required at compile time. The DPC++ compiler needs this
   flag to locate CUDA libdevice files.

5. **`MPICH_CXX=clang++`**: Required when compiling with the `mpicxx` wrapper.
   Without it, `mpicxx` uses `g++` which does not support `-fsycl`.

6. **oneAPI libraries**: Only the DPC++ compiler is included. Libraries such
   as oneDPL, oneMKL, and oneTBB are not part of this uenv and must be
   provided separately if needed.

## Tested on

- **Santis** (GH200, aarch64): single-node and multi-node MPI
- **Clariden** (GH200, aarch64): up to 2262 nodes (9048 GPUs), production runs

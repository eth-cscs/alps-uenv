# prgenv-gnu-dpcpp (AMD GPU / HIP)

> **Status: Experimental**

GNU compiler toolchain with Intel DPC++ SYCL compiler and HIP backend for
AMD GPU systems on Alps (gfx90a / MI250X, gfx942 / MI300A & MI300X).

## Overview

This recipe combines:
- The AMD GPU toolchain from `prgenv-gnu/7.2.0/amdgpu` (ROCm 7.2.0, HIP, RCCL, …)
- The Intel DPC++ SYCL compiler approach from `prgenv-gnu-dpcpp/25.11/gh200`

The Intel oneAPI binary distribution is x86_64 only and does not expose the
full HIP backend build path, so a custom Spack package (`llvmdpcpp`) builds
the compiler from the [intel/llvm](https://github.com/intel/llvm) `sycl`
branch directly, configured with `SYCL_ENABLE_BACKENDS=opencl;level_zero;hip`
and `LLVM_TARGETS_TO_BUILD=X86;SPIRV;AMDGPU`.

The environment provides:

- Intel DPC++ compiler (`clang++ -fsycl`) with HIP backend targeting gfx942, gfx90a
- Full ROCm 7.2.0 stack (rocBLAS, rocFFT, rocSOLVER, rocSPARSE, rocProfiler, …)
- HIP libraries (hipBLAS, hipBLASLt, hipFFT, hipSPARSE, hipRAND, hipDNN)
- GPU-aware MPI (cray-mpich@9.1.0 + ROCm GTL)
- RCCL + aws-ofi-rccl for multi-node GPU collectives
- Common development tools: Boost, CMake, FFTW, HDF5, NetCDF, OpenBLAS, Python, …

## Custom Spack package: llvmdpcpp

Located at `repo/packages/llvmdpcpp/package.py`. The build mirrors the
upstream `configure.py --hip` path from the
[GetStartedGuide](https://github.com/intel/llvm/blob/sycl/sycl/doc/GetStartedGuide.md#build-dpc-toolchain-with-support-for-hip-amd).
Key differences from the gh200 (CUDA) variant:

- `+hip` instead of `+cuda cuda_arch=90` — no `amdgpu_target` variant needed;
  architecture is chosen at application compile time via `--offload-arch=`
- `SYCL_ENABLE_BACKENDS` includes `hip` instead of `cuda`
- `LLVM_TARGETS_TO_BUILD` includes `AMDGPU` instead of `NVPTX`
- `lld` added to `LLVM_ENABLE_PROJECTS` (required for AMDGPU ELF code object linking)
- `SYCL_BUILD_UR_HIP_PLATFORM=AMD` (Unified Runtime HIP adapter platform)
- `UR_HIP_INCLUDE_DIR` / `UR_HIP_HSA_INCLUDE_DIR` / `UR_HIP_LIB_DIR` point to
  Spack's `hip` and `hsa-rocr-dev` prefixes (replaces the monolithic `UR_HIP_ROCM_DIR`
  that upstream assumes at `/opt/rocm`)
- libclc built as a **runtime target** using `LLVM_RUNTIME_TARGETS=default;amdgcn-amd-amdhsa-llvm`
  and `RUNTIMES_amdgcn-amd-amdhsa-llvm_LLVM_ENABLE_RUNTIMES=libclc` — not via
  per-arch `LIBCLC_TARGETS_TO_BUILD` entries

## Build

```bash
salloc -N 1 --time=240 -A <ACCOUNT>

mkdir -p /dev/shm/$USER
git clone https://github.com/eth-cscs/stackinator.git /dev/shm/$USER/stackinator
uv tool install --editable /dev/shm/$USER/stackinator
git clone git@github.com:eth-cscs/alps-cluster-config.git /dev/shm/$USER/alps-cluster-config

stack-config \
    --build /dev/shm/$USER/dpcpp-amdgpu \
    --recipe /path/to/recipes/prgenv-gnu-dpcpp/25.11/amdgpu \
    --system /dev/shm/$USER/alps-cluster-config/<cluster>

cd /dev/shm/$USER/dpcpp-amdgpu
env --ignore-environment PATH=/usr/bin:/bin:$(pwd -P)/spack/bin HOME=$HOME make store.squashfs -j144

cp store.squashfs /path/to/persistent/dpcpp-amdgpu.squashfs
```

## Usage

### Setup

```bash
uenv start --view=default /path/to/dpcpp-amdgpu.squashfs
export ROCM_PATH=$(ls -d /user-environment/linux-x86_64/llvm-amdgpu-*)
```

### Compile

```bash
# Non-MPI SYCL targeting AMD GPU
clang++ -std=c++17 -O3 -fsycl \
    -fsycl-targets=amdgcn-amd-amdhsa \
    -Xsycl-target-backend --offload-arch=gfx942 \
    source.cpp -o binary

# MPI (MPICH_CXX tells mpicxx to use DPC++ instead of g++)
MPICH_CXX=clang++ mpicxx -std=c++17 -O3 -fsycl \
    -fsycl-targets=amdgcn-amd-amdhsa \
    -Xsycl-target-backend --offload-arch=gfx942 \
    source.cpp -o binary
```

### Run

```bash
# single-node
./binary

# multi-node MPI
srun -n <procs> ./binary
```

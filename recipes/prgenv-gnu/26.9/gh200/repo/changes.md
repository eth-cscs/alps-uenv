# Changes vs. upstream spack-packages

The recipe pins spack-packages to
[`3b7fdffc24511b067b65540e0e9b3c89d07f8a7f`](https://github.com/spack/spack-packages/tree/3b7fdffc24511b067b65540e0e9b3c89d07f8a7f)
(develop, 4 Oct 2026; see `config.yaml`). The packages in `repo/packages/` override
their builtin counterparts. This file lists how each one differs from upstream
(`repos/spack_repo/builtin/packages/<name>` at that commit).

| Package                | Reason                                                       |
| ---------------------- | ------------------------------------------------------------ |
| `c_blosc`              | C23 build fix (GCC 15+)                                       |
| `osu_micro_benchmarks` | C23 build fix (GCC 15+)                                       |
| `cufftmp`              | Install layout / version audit                               |
| `nvshmem`              | New versions, cray-mpich perftests, Python bindings, Alps config |

## c_blosc

- **New patch** `0001-c23-bool-keyword.patch`, applied `when="@1.21.6"`.
  GCC 15 defaults to C23, where `bool` is a keyword, so `blosc/shuffle.c` can no
  longer do `typedef _Bool bool;`. The patch skips the typedef when
  `__STDC_VERSION__ >= 202311L`.
- `gcc.patch` and `test_forksafe.patch` are identical to upstream.

## osu_micro_benchmarks

- **New patch** `0001-c23-fix-synchronize_xccl_stream-call-sites.patch`, applied
  `when="@7.5.2"`.
  Under C23 (`-std=gnu23`, default in GCC 15), the empty parameter list `()` means "no
  parameters". The struct member `synchronize_xccl_stream` is declared `()`, but 9 call
  sites in `c/xccl` pass `nccl_stream` to it, which is now a hard error. The only
  implementation (`_synchronize_stream`) takes no arguments, so the patch removes the
  argument at those call sites.

## cufftmp

- Added `skip_version_audit = ["platform=darwin", "platform=windows"]`. Versions are
  only defined for the current host platform, so the audit must skip the others.
- `install()` no longer copies the whole tarball to the prefix with
  `install_tree(".", prefix)`. It now installs only:
  - `lib/` → `prefix.lib`
  - `include/` → `prefix.include.cufftmp` (headers go in a `cufftmp/` subdirectory,
    so they don't collide with the cuFFT headers shipped by CUDA)
  - `LICENSE` → `prefix`

## nvshmem

### Versions

- Added `3.8.0-0` (the version used in this recipe) and `3.6.5-0`.
- Removed `3.3.24` and `3.3.20`.
- `url_for_version`: versions `>= 3.6` are fetched from the GitHub release tarball
  (`https://github.com/NVIDIA/nvshmem/archive/refs/tags/v{version}.tar.gz`) instead
  of the NVIDIA redist server.

### Patches (new)

- `v3.4.5-perftest-mpich.patch`, applied `when="@3.4.5,3.6.5-0 +mpi"`.
  `perftest/common/utils.cu` looks up `ompi_mpi_comm_world` and `ompi_mpi_uint8_t`
  with `dlsym` and casts the resulting `void*` to `MPI_Comm`/`MPI_Datatype`. That only
  works with Open MPI. In MPICH (and cray-mpich) these handles are integers. With the
  patch, the `dlsym` path is used only when `NVSHMEM_MPI_IS_OMPI` is set; otherwise
  the code uses `MPI_COMM_WORLD`/`MPI_UINT8_T` directly.
- `v3.8.0-perftest-mpich.patch`, applied `when="@3.8.0-0 +mpi"`. The same fix,
  extended to the extra `ompi_mpi_info_null` lookup added in 3.8.0, which now falls
  back to `MPI_INFO_NULL`.
- `requirements-v3.6.5-0.patch`, applied `when="@3.6.5-0 +python"`. Fixes nvshmem4py
  packaging the same way as the Alps NGC containers (alps-extended-images):
  - drops `requirements_cuda11.txt` from `MANIFEST.in`
  - drops the `nvidia-nvshmem-cu12/13` runtime requirement (the library comes from
    Spack) and the pip `cuda-toolkit` build requirement
  - adds the missing `nvshmem.bindings._internal`, `nvshmem.bindings.device.cute`
    and `nvshmem.core.interop` packages (plus an empty `interop/__init__.py`)

### Python bindings (nvshmem4py)

- New variants: `python` (default off), and when `+python` is set: `mpi4py`
  (needs `+mpi`), `cupy` and `pytorch` (all default on).
- `conflicts("+python", when="@:3.2")`, plus `extendable = True` and
  `extends("python", when="+python")`.
- `+python` dependencies: `python@3.9:`, `py-pip`, `py-wheel`, `py-setuptools`,
  `py-cython@0.29.24:`, `py-numpy@1.26:`, `py-cuda-bindings` (run), and optionally
  `py-mpi4py`, `py-cupy`, `py-pytorch@2.6:` (run).
- `NVSHMEM_BUILD_PYTHON_LIB` follows the `python` variant (upstream always sets it
  to `False`). With `+python`, `Python3_EXECUTABLE` and `Python3_INCLUDE_DIR` are
  passed to CMake.
- `pin_wheel_build_inputs` (runs before `cmake`): replaces
  `nvshmem4py/scripts/find_python_versions.sh` so it reports only Spack's Python, and
  limits `CUDA_VERSIONS` in `nvshmem4py/CMakeLists.txt` to the CUDA major version of
  the spec.
- `install_python_wheel` (runs after `install`): installs the built nvshmem4py
  artifact from `build/dist` with
  `pip install --no-deps --no-build-isolation --no-index --prefix <prefix>`. It
  prefers a plain linux wheel, then a manylinux wheel, then an sdist.

### CMake configuration

- `NVSHMEM_BUILD_TESTS` is now `True` (upstream: `False`), so the perftests and
  tests are built and installed.
- Additional explicit CMake defines:
  - PMI: `NVSHMEM_PMI2_SUPPORT=1`, `NVSHMEM_DEFAULT_PMI2=1`,
    `NVSHMEM_PMIX_SUPPORT=0`, `NVSHMEM_DEFAULT_PMIX=0`
  - `NVSHMEM_MPI_IS_OMPI` = `1` with `^openmpi`, otherwise `0` (this drives the
    perftest patches above)
  - `NVSHMEM_NVTX=1`, `NVSHMEM_DISABLE_COLL_POLL=1`
  - set to `0`: `NVSHMEM_DEBUG`, `NVSHMEM_DEVEL`, `NVSHMEM_VERBOSE`,
    `NVSHMEM_TRACE`, `NVSHMEM_ENABLE_ALL_DEVICE_INLINING`,
    `NVSHMEM_GPU_COLL_USE_LDST`, `NVSHMEM_TEST_STATIC_LIB`,
    `NVSHMEM_TIMEOUT_DEVICE_POLLING`, `NVSHMEM_USE_DLMALLOC`,
    `NVSHMEM_DEFAULT_UCX`, `NVSHMEM_IBGDA_SUPPORT`,
    `NVSHMEM_IBGDA_SUPPORT_GPUMEM_ONLY`, `NVSHMEM_IBDEVX_SUPPORT`,
    `NVSHMEM_IBRC_SUPPORT`

### Runtime environment

- New `setup_run_environment` that sets the Alps/Slingshot defaults:
  - `NVSHMEM_REMOTE_TRANSPORT=libfabric`
  - `NVSHMEM_LIBFABRIC_PROVIDER=cxi`
  - `NVSHMEM_DISABLE_CUDA_VMM=1`

  `environments.yaml` also sets these variables for the uenv views.

### Other

- New imports: `os`, `glob`, `os.path.join as pjoin` (used by the Python hooks).

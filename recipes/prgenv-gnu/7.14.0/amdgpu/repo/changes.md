Changelog created by claude

# Tweaked package recipes — prgenv-gnu 7.14.0 amdgpu

Comparison of `repo/packages/*/package.py` in this recipe against the upstream
`spack-packages` recipes at the commit pinned in `config.yaml`:

- repo: https://github.com/spack/spack-packages.git
- commit: `988fbd949391fbde8381451c868dd39510aaebf9` (develop, 2026-11-25)

The pin, the recipe settings and the overrides follow the v3 recipe of
prgenv-gnu 7.2.3 (#391). The overrides shared with 7.2.3 are copied from that
recipe, which rebased them on this commit; their 7.2-only tweaks have no
effect here. The overrides marked "new in 7.14.0" are specific to this recipe.

On the previous pin (`1d20553`, `unify: when_possible`), the CI build passed on
`fc0e50d` for `gfx90a` and `gfx942`, and 52 of 56 CI tests passed.
`RocHPL_medium`, `RocHPL_large` and the `rccl-tests` `all_reduce` and
`sendrecv` tests failed, cause unknown. The current state is not yet built.

Changed in `compilers.yaml`:

- `llvm-amdgpu: spec: "%c,cxx=gcc@13"`. Without it the llvm-amdgpu group is
  built with the system gcc 12, and its `clang++.cfg` points HIP compiles at
  the gcc 12 libstdc++. On 7.2.3 this broke miopen-hip on `nlohmann/json.hpp`.
  Stackinator compiler groups get only `needs: [gcc]`, so they don't inherit
  the gcc 13 preference.

Overrides from 7.2.3 that were dropped:

- `composable_kernel`: installed a pre-built 7.2.3 binary. It now builds from
  source, see the `composable_kernel` section below.
- `hipdnn`: its only tweak was a patch for `@7.2.3`. Upstream disables
  clang-tidy for `@7.13.0:`. The 7.2.3 recipe has a new `hipdnn` override, but
  upstream already uses `flatbuffers~shared` for `@7.13:`, and the 7.14 build
  passed without `HIP_DNN_GENERATE_SDK_HEADERS=OFF`.
- `libdrm`: capped the version at 2.4.124, but upstream `amdsmi@7.13:` requires
  `libdrm@2.4.131:`.

Overrides in the 7.2.3 recipe that are not used here:

- `hipblaslt`: drops `spdlog@:1.14` for `@7.1:7.2` only.
- `rccl_tests`: restores the old `ROCm/rccl-tests` package because upstream
  now has only rocm-systems versions from 7.14.0 on. This recipe uses upstream
  `rccl-tests@7.14.0` instead of the `git.6405c76...=develop` commit.

Removed from `environments.yaml`:

- `rocm-openmp-extras`: AMD has no 7.14 release (`aomp`, `aomp-extras` and `flang`
  stop at `rocm-7.2.4`), so it concretized to 7.2.3 and pulled in
  `llvm-amdgpu@7.2.3`. `llvm-amdgpu@7.13:` builds OpenMP and offload itself.

Changed in `environments.yaml`:

- `unify: true` instead of `unify: when_possible` with `duplicates: full`, as
  in 7.2.3. There, `when_possible` pulled in a second ROCm stack and silently
  dropped hipblaslt from rocblas and miopen-hip. With `unify: true` every
  package has one version, and `hip@7.14.0` pins the whole ROCm stack, so
  `rocprofiler-systems` no longer needs `@7.14.0`.
- `python@3.12` as a root spec: the `^python@3.12.15` entry under `variants:`
  had no effect on 7.2.3 (the env used python 3.14).
- `fmt@12.1`: `rocprofiler-compute@7.13:` requires exactly this version, so
  with `unify: true` it is the only possible one. It also fits
  `rocprofiler-sdk@7.14:` (`fmt@:12.1`) and `hipblaslt` (`fmt@11.1:`), so
  `rocprofiler-sdk` does not need `+internal-fmt` as on 7.2.3.
- `rocprofiler-systems +internal-dyninst +rocm`: the global `+rocm` in
  `variants:` is only a preference, and the solver picked `~rocm`, which drops
  the `rocprofiler-sdk` dependency, so the build failed.
- `rccl-tests +mpi`: same problem with the global `+mpi`. With `~mpi` each
  Slurm task ran as its own rank 0 and reported bogus bandwidths. The upstream
  package requires `%cxx=llvm-amdgpu`, and `unify: true` allows only one
  cray-mpich, so the earlier `%cxx=llvm-amdgpu@7.14.0 ^cray-mpich@9.2.1 +rocm
  %gcc` is dropped. With `when_possible` that constraint was needed to avoid a
  second `cray-mpich@8.1.32` built with `rocmcc`.
- `rocm-cmake`, `rocm-core`, `roctracer-dev-api`: dropped `%cxx=gcc`, gcc is
  already preferred.

## amdsmi

- `depends_on("python@3.6:")` → `depends_on("python@3.6:", type=("build", "run"))`.
- Adds `setup_run_environment()`, prepending `share/amd_smi` to `PYTHONPATH`.

Why: the amdsmi Python module is installed outside site-packages, so only the
`amd-smi` CLI finds it without this.

## aws_ofi_nccl

- Adds version `1.20.0`.
- Adds `conflicts` for `+rocm` with `@1.18:1.19` and for `+tests` with `+rocm`.
- `depends_on("hip", when="+rocm")` → `depends_on("hip +rocm", when="+rocm")`.
- Adds HSA include and library paths in `setup_build_environment()`, and passes
  `--without-cuda` for `+rocm` builds.

Why: the 1.18/1.19 tarballs are missing `nccl_ofi_rocm.h`, and without the HSA
paths configure silently compiles out DMA-BUF support for Spack-built ROCm.

## composable_kernel (new in 7.14.0)

- Subclasses the builtin package. Sets `MIOPEN_REQ_LIBS_ONLY=ON` and
  `CK_PARALLEL_COMPILE_JOBS=24`.

Why: the full build for `gfx90a;gfx942` has 2345 objects and reached about 612
in 9 hours, then a compile was OOM-killed on a 502 GB node at `-j64`. Only
`miopen-hip` depends on it, and MIOpen needs only `device_conv_operations`. The
installed package therefore has no GEMM, MHA, contraction or reduction
instances.

## llvm_amdgpu

- `depends_on("python", type="build")` → `depends_on("python@3.12.15", type="build")`.

Why: added to build llvm-amdgpu only once (commit `Added dependency to
python@3.12.13 to llvm-amdgpu to built it only once`). 3.12.15 is the only
Python 3.12 at the pinned commit, and matches `^python@3.12.15` in
`environments.yaml`.

- Adds `depends_on("zstd", type="link")` and sets `LLVM_ENABLE_ZSTD=FORCE_ON`.

Why: without zstd, `clang-offload-bundler --compress` falls back to zlib, and
on this stack those bundles fail to decompress (`zlib error: Z_DATA_ERROR`,
[ROCm/rocm-libraries#6085](https://github.com/ROCm/rocm-libraries/issues/6085)).
composable-kernel compresses its bundles, so MIOpen's CK kernels would not
load. AMD's own packages compress with zstd. comgr gets its decompression from
these LLVM libraries, so it needs zstd to read them
([#387](https://github.com/eth-cscs/alps-uenv/issues/387)).

## miopen_hip

- `depends_on("boost@1.67.0:1.73.0")` → only `when="@:7.1"`, and
  `depends_on("boost@1.83:", when="@7.2:")`.

Why: with `unify: true` the cap conflicts with the root `boost@1.88.0`.
MIOpen 7.2 builds against boost 1.83 (`requirements.txt`). Upstream lifts the
cap only for `@10.1:`.

- Adds `args.append(self.define_from_variant("GPU_TARGETS", "amdgpu_target"))`
  at the end of `cmake_args()`.

Why: upstream does not forward the `amdgpu_target` variant to CMake's
`GPU_TARGETS`, which MIOpen uses to select its per-architecture kernels.

## py_barectf

- Switches from a PyPI release (`barectf-3.1.2.tar.gz`) to a **git checkout**
  of a specific commit on `master`
  (`e16d289546bb4f6b0d909f79b8d6188eabe32640`, labeled version `3.1.2-fix`).
- Drops upstream's `fix-pkg-resources.patch`, which covers the same problem.
- Adds `homepage`/`git` attributes (upstream only has `pypi`).
- Broadens `depends_on("py-poetry-core", type="build")` to
  `type=("build", "run")`.
- Adds deps not present upstream: `py-setuptools`, `py-termcolor@1.1:`,
  `py-pyyaml@6.0:`, `py-jsonschema@3.2:`, `py-jinja2@3.0:`.

Why: the 3.1.2 release imports `pkg_resources`, which fails on Python 3.12. The
commit replaces it with `importlib.resources`.

## rocblas

- Adds `offload_bundler_path.patch` (`@7.0:7.1` in `Tensile`, `@7.2:` in
  `shared/tensile`) and passes `Tensile_OFFLOADBUNDLER`.

Why: points Tensile at the `clang-offload-bundler` from llvm-amdgpu.
`0010-disable-tensile-co-compression.patch` was removed, as in 7.2.3: with
llvm-amdgpu built with zstd (see `llvm_amdgpu`), Tensile's code objects are
zstd-compressed, like those in AMD's own packages.

## rocprofiler_compute (new in 7.14.0)

- Subclasses the builtin package. Sets `ROCM_PATH` to the `rocprofiler-sdk`
  prefix during the build.

Why: its CMake does `set(CMAKE_PREFIX_PATH $ENV{ROCM_PATH} "/opt/rocm/")`, so it
picks up the older SDK in `/opt/rocm` on the build node, which lacks
`rocprofiler_counter_config_id_t`.

## rocprofiler_systems

- Adds a new variant `internal-boost` (default `True`, "build internal
  boost").
- The two external `boost@:1.88...` dependencies are gated with
  `~internal-boost`.
- When `+internal-boost`, passes
  `self.define_from_variant("ROCPROFSYS_BUILD_BOOST", "internal-boost")` to
  CMake.
- `-lintl` for `@6.3:7.2` instead of `@6.3:7.1` (from 7.2.3; 7.14 is covered
  upstream by `@7.14:`).

Why: avoids Spack's `boost` for this package. `ROCPROFSYS_BUILD_BOOST` was not
found in the rocprofiler-systems CMake files checked at `therock-7.14`, so this
variant may only remove the `boost` dependency. The package builds with
`+internal-boost`.

## zstd

- `build_system("cmake", "makefile", default="makefile")` →
  `default="cmake"`.
- Adds `args.append(self.define("CMAKE_POSITION_INDEPENDENT_CODE", True))` in
  `CMakeBuilder.cmake_args()`.
- (Trivial) one added whitespace-only line at the end of `cmake_args()` — no
  functional effect.

Why: switches zstd to build via CMake by default (rather than the Makefile
build) and forces `-fPIC`. The commit that added this (`Trying to build zstd
with -fPIC`) does not record what failed; a likely reason is that a static
zstd is linked into a shared library elsewhere in the stack.

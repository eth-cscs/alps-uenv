Changelog created by claude

# Tweaked package recipes — prgenv-gnu 7.14.0 amdgpu

Comparison of `repo/packages/*/package.py` in this recipe against the upstream
`spack-packages` recipes at the commit pinned in `config.yaml`:

- repo: https://github.com/spack/spack-packages.git
- commit: `1d20553aa70019bb6c46cfecc5d7b6bf1e0dc5d3` (develop, 2026-10-31)

Each override is the upstream recipe at this commit with the tweaks from the
7.2.3 recipe re-applied, plus the overrides marked "new in 7.14.0". The recipe
builds completely: the CI build passes on `fc0e50d` for `gfx90a` and `gfx942`.
In the CI tests, 52 of 56 pass. `RocHPL_medium`, `RocHPL_large` and the
`rccl-tests` `all_reduce` and `sendrecv` tests still fail, cause unknown.

Overrides from 7.2.3 that were dropped:

- `composable_kernel`: installed a pre-built 7.2.3 binary. It now builds from
  source, see the `composable_kernel` section below.
- `hipdnn`: its only tweak was a patch for `@7.2.3`. Upstream disables
  clang-tidy for `@7.13.0:`.
- `libdrm`: capped the version at 2.4.124, but upstream `amdsmi@7.13:` requires
  `libdrm@2.4.131:`.

Removed from `environments.yaml`:

- `rocm-openmp-extras`: AMD has no 7.14 release (`aomp`, `aomp-extras` and `flang`
  stop at `rocm-7.2.4`), so it concretized to 7.2.3 and pulled in
  `llvm-amdgpu@7.2.3`. `llvm-amdgpu@7.13:` builds OpenMP and offload itself.

Changed in `environments.yaml`:

- `rocprofiler-systems@7.14.0 +internal-dyninst +rocm`: the global `+rocm` in
  `variants:` is only a preference, and the solver picked `~rocm`, which drops
  the `rocprofiler-sdk` dependency, so the build failed. `@7.14.0` keeps it on
  the ROCm release. Upstream `10.0.0` also declares the dependency, so the
  version was not the cause (commit `a280001` says otherwise).
- `rccl-tests ... +mpi`: same problem with the global `+mpi`. With `~mpi` each
  Slurm task ran as its own rank 0 and reported bogus bandwidths.
- `rccl-tests ... ^cray-mpich@9.2.1 +rocm %gcc`: without it, `+mpi` adds a
  second `cray-mpich@8.1.32` built with `rocmcc`, which fails to install
  ("Unsupported toolchain"). `%c,cxx,fortran=gcc` does not concretize, while
  `%gcc` does and gives `%fortran=gcc`. This still installs a second
  `cray-mpich@9.2.1` prefix (`%fortran=gcc %c,cxx=rocmcc`), used only by
  `rccl-tests`.

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

## miopen_hip

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
- Adds `0010-disable-tensile-co-compression.patch` for `@7.2: +tensile`.

Why: the first patch points Tensile at the `clang-offload-bundler` from
llvm-amdgpu. The commit that added the second records no reason. Both apply to
the `therock-7.14` sources, the second with an offset and fuzz, and rocblas
builds with both.

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
- (Trivial) local file lacks the trailing newline upstream has.

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

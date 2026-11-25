Changelog created by claude

# Tweaked package recipes — prgenv-gnu 7.2.3 amdgpu

Comparison of `repo/packages/*/package.py` in this recipe against the upstream
`spack-packages` recipes at the commit pinned in `config.yaml`:

- repo: https://github.com/spack/spack-packages.git
- commit: `988fbd949391fbde8381451c868dd39510aaebf9` (develop, 2026-11-25)

The recipe uses the v3 recipe format (Stackinator 7, Spack `releases/v1.2`).
Each override is the upstream recipe at this commit with the earlier tweaks
re-applied.

Changed in `compilers.yaml`:

- `llvm-amdgpu: spec: "%c,cxx=gcc@13"`. Without it the llvm-amdgpu group is
  built with the system gcc 12, and `clang++.cfg` sets
  `--gcc-install-dir=/usr/lib64/gcc/x86_64-suse-linux/12`. With the gcc 12
  libstdc++ headers, `-x hip` fails to compile `nlohmann/json.hpp`
  (`cannot convert 'const nlohmann::basic_json<>' to 'value_t'`), which broke
  miopen-hip. The 7.2.3 recipe on main had the compiler built with gcc 13.

Changed in `environments.yaml`:

- `unify: true` instead of `unify: when_possible` with `duplicates: full`.
  With `when_possible` the root `hipblaslt` concretized to 10.0.0 and pulled in
  a second ROCm stack (hip, hsa-rocr-dev, llvm-amdgpu, comgr, ... @10.0.0),
  while rocblas and miopen-hip silently fell back to `~hipblaslt`. The env
  now has a single version of every package.
- `python@3.12`: the `^python@3.12.15` entry under `variants:` had no effect
  (the env used python 3.14.9).
- `fmt@11.1.3`: the version rocroller (hipblaslt) 7.2.3 fetches itself.
- `rocprofiler-sdk +internal-fmt`: rocprofiler-sdk 7.2 needs `fmt@:10`
  otherwise.
- `rocprofiler-systems +internal-dyninst +rocm`: the global `+rocm` in
  `variants:` is only a preference, and with `~rocm` the build fails.
- `rccl-tests ... +mpi %cxx=llvm-amdgpu@7.2.3`: same problem with the global
  `+mpi`. The `^cray-mpich@9.2.1 +rocm %gcc` constraint is not needed with
  `unify: true`, which allows only one cray-mpich.
- `rocm-cmake`, `rocm-core`, `roctracer-dev-api`: dropped `%cxx=gcc`, gcc is
  already preferred. Without it the concretization is the same.
- `rocblas +tensile`: dropped `^py-msgpack %cxx=gcc`, py-msgpack no longer
  depends on cxx.

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

## composable_kernel

- Subclasses the builtin package and builds from source. Sets
  `MIOPEN_REQ_LIBS_ONLY=ON` and `CK_PARALLEL_COMPILE_JOBS=24`.

Why: this recipe used to install a prebuilt 7.2.3 package taken from Arch
Linux. Its code-object bundles are zstd-compressed, but `llvm-amdgpu` (and
therefore `comgr`) is built without zstd. MIOpen links these bundles
statically, so the first CK convolution kernel fails to unbundle and the
process segfaults ([#387](https://github.com/eth-cscs/alps-uenv/issues/387)).
Building with the stack's own toolchain fixes this. Offload compression stays
on: without it the fat binaries push `libMIOpen.so` past 2 GiB and its link
fails with `relocation R_X86_64_PC32 out of range` against the static
`librockCompiler.a`. This needs `llvm-amdgpu` built with zstd (see below), since
the bundler's zlib fallback produces bundles that fail to decompress. `MIOPEN_REQ_LIBS_ONLY` is taken from the 7.14.0
recipe: without it the full build for `gfx90a;gfx942` takes far too long. Only
`miopen-hip` depends on CK, and it needs only `device_conv_operations`, so the
installed package has no GEMM, MHA, contraction or reduction instances.

## hipblaslt

- `depends_on("spdlog@:1.14", when="@7.1:7.2")` and
  `depends_on("spdlog", when="@7.13:")` → `depends_on("spdlog", when="@7.1:")`.

Why: `spdlog@:1.14` needs `fmt@:10`, and the same recipe needs `fmt@11.1:`,
so upstream `hipblaslt@7.2.3` cannot be concretized. The cap was added in
spack/spack-packages#5309. rocroller 7.2.3 itself fetches fmt 11.1.3 and
spdlog `v1.x`.

## hipdnn

- Adds a second patch, `0002-disable-clang-tidy-checks.patch`, applied
  `when="@7.2.3"` with `working_dir="projects/hipdnn"`.
- The patch extends `.clang-tidy`'s disabled-checks list with
  `-portability-avoid-pragma-once`, `-modernize-use-scoped-lock`, and
  `-readability-use-concise-preprocessor-directives`.

Why: hipdnn builds with `WarningsAsErrors: "*"` in `.clang-tidy`, so any
clang-tidy diagnostic fails the build. These three checks were apparently
firing (likely due to compiler/clang-tidy version differences) and needed to
be suppressed to get 7.2.3 to build.

## libdrm

- Drops `version("2.4.134", ...)` and `version("2.4.131", ...)`; only
  `2.4.124` and older remain.

Why: `amdsmi@:7.2` needs `libdrm@:2.4.124`
([ROCm/amdsmi#167](https://github.com/ROCm/amdsmi/issues/167)); upstream now
says so too. Removing the newer versions keeps a single libdrm in the stack.

## llvm_amdgpu

- `depends_on("python", type="build")` → `depends_on("python@3.12.15", type="build")`.

Why: llvm-amdgpu is built in its own spec group, before the env. Without the
pin it builds with the newest Python (3.15.1), with the pin it uses the same
Python as the env. Either way llvm-amdgpu is built only once.

- Adds `depends_on("zstd", type="link")` and sets `LLVM_ENABLE_ZSTD=FORCE_ON`.

Why: without zstd, `clang-offload-bundler --compress` falls back to zlib, and
on this stack those bundles fail to decompress (`zlib error: Z_DATA_ERROR`,
[ROCm/rocm-libraries#6085](https://github.com/ROCm/rocm-libraries/issues/6085)).
That broke rocblas's Tensile kernels, and was worked around by disabling
compression there. comgr gets its
decompression from these LLVM libraries, so without zstd it also cannot read
zstd-compressed bundles ([#387](https://github.com/eth-cscs/alps-uenv/issues/387)).

## miopen_hip

- `depends_on("boost@1.67.0:1.73.0")` → only `when="@:7.1"`, and
  `depends_on("boost@1.83:", when="@7.2:")`.

Why: with `unify: true` the cap conflicts with the root `boost@1.88.0`.
MIOpen 7.2.3 itself builds against boost 1.83 (`requirements.txt`), and
only needs `filesystem`, found with `find_package(Boost CONFIG)`.

- Adds `args.append(self.define_from_variant("GPU_TARGETS", "amdgpu_target"))`
  at the end of `cmake_args()`.

Why: matches this repo's commit `miopen-hip, set GPU_TARGETS` — upstream never
forwards the `amdgpu_target` variant to CMake's `GPU_TARGETS`, so without this
the build would fall back to MIOpen's default target list instead of the
gfx90a/gfx942 targets this stack builds for.

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
`0010-disable-tensile-co-compression.patch` was removed: with llvm-amdgpu built
with zstd (see `llvm_amdgpu`), Tensile's compressed code objects are
zstd-compressed, like those in AMD's own packages.

## rocprofiler_compute

- `depends_on("fmt@12.1", when="@7.1:")` → `when="@7.13:"`.

Why: only the 7.13+ sources build against fmt (`src/lib/external`, see
`patch()`). The 7.2.3 CMake does not use fmt, and the pin conflicts with
`fmt@11.1.3`.

## rocprofiler_systems

- Adds a new variant `internal-boost` (default `True`, "build internal
  boost").
- The two existing external `boost@:1.88...` dependencies are now gated with
  `~internal-boost` (only pulled in when internal boost is *not* used).
- When `+internal-boost`, passes
  `self.define_from_variant("ROCPROFSYS_BUILD_BOOST", "internal-boost")` to
  CMake so rocprofiler-systems builds its own bundled Boost instead.
- (Trivial) local file lacks the trailing newline upstream has.

Why: avoids depending on Spack's external `boost` package (version/variant
conflicts are a common pain point for Boost in large environments) by letting
rocprofiler-systems build its own internal Boost by default.

## zstd

- `build_system("cmake", "makefile", default="makefile")` →
  `default="cmake"`.
- Adds `args.append(self.define("CMAKE_POSITION_INDEPENDENT_CODE", True))` in
  `CMakeBuilder.cmake_args()`.
- (Trivial) one added blank/whitespace-only line — no functional effect.

Why: switches zstd to build via CMake by default (rather than the Makefile
build) and forces `-fPIC`, most likely because zstd is linked into a shared
library elsewhere in the stack and needed position-independent code.

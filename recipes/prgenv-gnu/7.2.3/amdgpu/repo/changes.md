Changelog created by claude

# Tweaked package recipes — prgenv-gnu 7.2.3 amdgpu

Comparison of `repo/packages/*/package.py` in this recipe against the upstream
`spack-packages` recipes at the commit pinned in `config.yaml`:

- repo: https://github.com/spack/spack-packages.git
- commit: `236a1bf4c0d3418f050915eea4c815061f3d7e81` (develop, 2026-05-28)

## composable_kernel

- Subclasses the builtin package and builds from source. Sets
  `MIOPEN_REQ_LIBS_ONLY=ON`, `CK_PARALLEL_COMPILE_JOBS=24` and
  `DISABLE_OFFLOAD_COMPRESS=ON`.

Why: this recipe used to install a prebuilt 7.2.3 package taken from Arch
Linux. Its code-object bundles are zstd-compressed, but `llvm-amdgpu` (and
therefore `comgr`) is built without zstd. MIOpen links these bundles
statically, so the first CK convolution kernel fails to unbundle and the
process segfaults ([#387](https://github.com/eth-cscs/alps-uenv/issues/387)).
Building with the stack's own toolchain fixes this. Compression is turned off,
as for Tensile in `rocblas`. `MIOPEN_REQ_LIBS_ONLY` is taken from the 7.14.0
recipe: without it the full build for `gfx90a;gfx942` takes far too long. Only
`miopen-hip` depends on CK, and it needs only `device_conv_operations`, so the
installed package has no GEMM, MHA, contraction or reduction instances.

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

- Drops `version("2.4.131", ...)`; only `2.4.124` and older remain.
- (Trivial) local file lacks the trailing newline upstream has — no functional
  effect.

Why: likely 2.4.131 didn't build/resolve correctly for this stack, so it was
pinned back to the last known-good version (2.4.124).

## llvm_amdgpu

- `depends_on("python", type="build")` → `depends_on("python@3.12.13", type="build")`.

Why: pins the exact Python version used at build time instead of letting
Spack's concretizer pick one, presumably to match the Python already selected
elsewhere in this environment and avoid a second/incompatible Python being
pulled in.

## miopen_hip

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
- Adds `homepage`/`git` attributes (upstream only has `pypi`).
- Broadens `depends_on("py-poetry-core", type="build")` to
  `type=("build", "run")`.
- Adds new runtime/build deps not present upstream: `py-setuptools`,
  `py-termcolor@1.1:`, `py-pyyaml@6.0:`, `py-jsonschema@3.2:`, `py-jinja2@3.0:`.

Why: the `-fix` version suffix and the pin to a specific unreleased commit
indicate the 3.1.2 PyPI release had a bug that's fixed on `master` but not yet
tagged/released; building from source also exposed missing runtime deps that
the sdist install had been hiding, so they were added explicitly.

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

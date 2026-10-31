Changelog created by claude

# Tweaked package recipes — prgenv-gnu 7.2.3 amdgpu

Comparison of `repo/packages/*/package.py` in this recipe against the upstream
`spack-packages` recipes at the commit pinned in `config.yaml`:

- repo: https://github.com/spack/spack-packages.git
- commit: `236a1bf4c0d3418f050915eea4c815061f3d7e81` (develop, 2026-05-28)

## composable_kernel

Completely rewritten, not just patched. Upstream builds composable_kernel
from source as a `CMakePackage`/`ROCmLibrary` (with dozens of versions and a
large kernel-instantiation build). The local recipe instead:

- Switches the base class to `Package` (generic) and installs a **pre-built
  binary tarball** (`file:///capstor/scratch/cscs/simonpi/binary-packages/
  composable-kernel-7.2.3-1-x86_64.pkg.tar.gz`) via `install_tree("opt/rocm",
  prefix)` instead of compiling.
- Only version `7.2.3` is defined (all older upstream versions dropped).
- `amdgpu_targets` is now a hardcoded tuple (copied from `ROCmPackage`) instead
  of referencing `ROCmPackage.amdgpu_targets`, since the package no longer
  inherits from `ROCmPackage`.
- Still declares `depends_on("hip+rocm@7.2.3")` / `depends_on("llvm-amdgpu@7.2.3")`
  for consistency with dependents, even though nothing is actually compiled.
- All CMake args, `root_cmakelists_dir`, `setup_build_environment`, and the
  `0001-mark-kernels-maybe-unused.patch` are gone (no longer relevant to a
  binary install).

Why: git history on this directory (`use binary package for composable-kernel`,
plus several earlier "Trying to fix amdgpu_targets" / patch commits) shows the
from-source build was repeatedly broken/unworkable for the full multi-arch
target set, so it was replaced with a binary package built out-of-band and
installed verbatim. The untracked `package_orig.py` left in the directory is
the last from-source attempt before that switch (it only differs from
upstream by one extra patch, `0002-multi-gpu-arch.patch`, applied to
`projects/composablekernel` for `@7.2.3` — that patch file no longer exists in
the repo).

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

# PyTorch 2.6

This `uenv` recipe was designed with the intention of being able to run
`Megatron-LM` based pre-training workloads out of the box. Thus, it comes with
batteries included and does not just provide the bare `PyTorch` framework. The
recipe is based on `spack`'s latest stable release `v0.23.1`. Thus, many
packages had to be backported in order to achieve compatibility with
`PyTorch@2.6` and `python@13`.

## Package Updates

The following packages have been updated manually. The reasons are varied, but
include for example
- fixes to make `spack.build_systems.python` work by fully qualifying the name
- patches to make packages compatible with `python@13`
- upgrades to `py-torch@2.6`

Many of the changes are taken from the spack `develop` branch and will likely
land in the next version. However, there are also some fixes with are not
upstreamed (yet).

### hdf5
- added new variant `direct-vfd` to enable `O_DIRECT` virtual file driver

### faiss
- fix `python` error: import `build_systems` module from `spack` and use
  qualified `build_systems.python`

### nvtx
- fix `python` error: import `build_systems` module from `spack` and use
  qualified `build_systems.python`

### py-cython
- pulled from `develop` to support `python@13`
- see https://github.com/spack/spack/pull/47714

### py-sympy
- upgraded to version 1.13.1
- needed for `py-torch`, see https://github.com/spack/spack/pull/48951

### py-torch
- upgraded to 2.6.0 using https://github.com/spack/spack/pull/48794
    - dependencies updated
    - use system `nvtx` library
    - patch for `gloo`
    - patch for `xnnpack` on `aarch64`
    - requires updating
        - `cpuinfo` (new version)
        - `py-pybind11` (new version)
        - `py-torch-nvidia-apex` (version deprecation, patches)
        - `py-torchaudio` (new version)
        - `py-torchvision` (new version)
- enabled built-in flash attention

### py-torch-nvidia-apex
- version update (see `py-torch`)
- refactoring of variants
- enabled submodules (needed for cutlass)

### sentencepiece
- version update
- disable `TCMalloc` (added variant set to false by default) because of runtime
  errors

### py-sentencepiece
- version update

### py-sentry-sdk
- version update
- `pypi` naming scheme changed
    - underscore instead of hyphen in tar filename but not folder (why???)
    - `sentry-sdk/sentry-sdk-0.17.6.tar.gz` vs
      `sentry-sdk/sentry_sdk-2.0.0.tar.gz`

### py-triton
- new versions are no longer tagged and `pypi` does not provide source
  distributions: added commit hashes based on commit logs
- refactoring of dependencies
- patch usage of `bdist_wheel`: is part of `setuptools` in more recent versions
  instead `pypa`
- set environment variables:
    - force triton to use system `cuda` libraries and system `pybind11`
    - make a temporary triton home directory for downloads
    - `MAX_JOBS` for number build jobs
- define new `PythonPipBuilder` class which builds from top level directory
    - starting the build process from the `python` subdirectory causes errors
    - `spack` does not provide an option to specify this in the `PythonPackage`
        - if you define the `build_directory`, it will change directories
          instead of adding the directory as last argument to `pip`

### py-transformer-engine
- refactored dependencies
- added `cudnn` dependency
- set environment variables
    - force system `cudnn`
    - set `CUDAARCHS`
- patch to allow `python@13`

### py-zarr
- update version, see https://github.com/spack/spack/pull/48786
    - requires new package: `py-donfig`
    - requires new version of `py-numcodecs`

### py-tokenizers
- update version

### py-huggingface-hub
- update version, see https://github.com/spack/spack/pull/47600
    - new variant `hf` requires new package `py-hf-transfer`

### py-transformers
- update version

### py-pydantic, py-pydantic-core
- update version, see https://github.com/spack/spack/pull/47771
- needed for `python@13`

### py-safetensors
- update version, see https://github.com/spack/spack/pull/47774
- needed for `python@13`

### py-wandb
- update version, see https://github.com/spack/spack/pull/43891

### py-dockerpy-creds
- umaintained, needs patch to fix `distutils` in newer python versions, see
  https://github.com/shin-/dockerpy-creds/pull/15
- needed by `py-wandb`

## Full Diff w.r.t. v0.23.1

    diff --git i/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py w/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py
    index ed1788feea..0253c031f8 100644
    --- i/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py
    +++ w/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py
    @@ -25,3 +25,9 @@ class PyDockerpyCreds(PythonPackage):
         depends_on("python@2.0:2.8,3.4:", type=("build", "run"))
         depends_on("py-setuptools", type="build")
         depends_on("py-six", type=("build", "run"))
    +
    +    patch(
    +        "https://patch-diff.githubusercontent.com/raw/shin-/dockerpy-creds/pull/15.patch?full_index=1",
    +        sha256="e1a9f6312636db956a8c2136c5c5ab99d7351ae91de9bdbd4fe7718cf3665561",
    +        when="@0.4.0",
    +    )
    diff --git i/var/spack/repos/builtin/packages/py-wandb/package.py w/var/spack/repos/builtin/packages/py-wandb/package.py
    index 6d0949338c..23a3b05d8d 100644
    --- i/var/spack/repos/builtin/packages/py-wandb/package.py
    +++ w/var/spack/repos/builtin/packages/py-wandb/package.py
    @@ -17,11 +17,11 @@ class PyWandb(PythonPackage):
     
         license("MIT")
     
    +    version("0.16.6", sha256="86f491e3012d715e0d7d7421a4d6de41abef643b7403046261f962f3e512fe1c")
         version("0.13.9", sha256="0a17365ce1f18306ce7a7f16b943094fac7284bb85f4e52c0685705602f9e307")
     
         depends_on("py-setuptools", type=("build", "run"))
     
    -    depends_on("py-pathtools", type=("build", "run"))
         depends_on("py-setproctitle", type=("build", "run"))
         depends_on("py-appdirs@1.4.3:", type=("build", "run"))
         depends_on("py-protobuf@3.19:4", type=("build", "run"))
    @@ -29,10 +29,15 @@ class PyWandb(PythonPackage):
         depends_on("py-typing-extensions", type=("build", "run"), when="^python@:3.9")
     
         depends_on("py-pyyaml", type=("build", "run"))
    -    depends_on("py-click@7:", type=("build", "run"))
    +    depends_on("py-click@7:", type=("build", "run"), when="@0.13")
    +    depends_on("py-click@7.1:", type=("build", "run"), when="@0.15.5:")
         conflicts("^py-click@8.0.0")
         depends_on("py-gitpython@1:", type=("build", "run"))
    +    conflicts("^py-gitpython@3.1.29")
         depends_on("py-requests@2", type=("build", "run"))
         depends_on("py-psutil@5:", type=("build", "run"))
         depends_on("py-sentry-sdk@1.0.0:", type=("build", "run"))
         depends_on("py-dockerpy-creds@0.4.0:", type=("build", "run"))
    +
    +    # Historical dependencies
    +    depends_on("py-pathtools", type=("build", "run"), when="@:0.15")

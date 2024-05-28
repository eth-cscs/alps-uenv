# Using uenvs as upstream Spack instances

User-environments (uenvs) are built with [Spack] using the [Stackinator] tool. Therefore, a `uenv` is tightly coupled with [Spack] and can be used as an upstream [Spack] instance (see [Chaining Spack Installations] for more details).

!!! note
    While this guide tries to explain everything step-by-step, it might be difficult to follow without any knowledge of [Spack]. Please have a look at [Spack Basic Usage] for a short introduction to [Spack].

The uenv of a supported application contains all the dependencies to build the software with a particular configuration. In [Spack], such configuration is defined by a [spec] (see [Spack Basic Usage] for more details). Most uenvs already provide modules or [Spack Filesystem Views] which allow to manually build the same configuration. However, it is possible that you want to build or develop an application with a different configuration. To avoid re-building the whole uenv, you can re-use what is already there and build your new configuration using [Spack]. 

This guide explains a _developer workflow_ allowing to either build your own package with [Spack], or use [Spack] to build all the dependencies and provide a build environment for the package.

!!! note
    This guide assumes that you have a local installation of [Spack]. If you don't have [Spack] installed, follow [Spack Getting Started].

!!! warning
    Avoid installing [Spack] on `HOME`. Packages are installed within the `spack/` folder, and you might quickly run out of space.

## Example: CP2K

As an example, we will consider [CP2K] as the application we want to develop. While the uenv for [CP2K] we provide is rather complete, let's assume for simplicity that the provided configuration is very bare bone:

```
cp2k@2024.1 +cuda cuda_arch=80
```

This [spec] defines a build of [CP2K] version `2024.1` with CUDA acceleration. All other dependencies and features are defined by the default values in the [CP2K Spack package].

## Set uenv as upstream Spack instance

Activate the uenv. Here we assume the uenv described above is called `cp2k/2024.1` and it is already deployed:

```bash
uenv image pull cp2k/2024.1
uenv start cp2k/2024.1
```

With the uenv active, we can now tell our local [Spack] instance to use the uenv as an upstream [Spack] instance (see [Chaining Spack Installations] for more details):

```bash
export SPACK_SYSTEM_CONFIG_PATH=/user-environment/config/
```

!!! note
    We assumed here that the uenv is mounted in the standard location `/user-environment/`. If it is mounted in a non-standard location, adjust the previous command accordingly.

## Building your own version 

Let's assume we want to have a version of [CP2K] what uses the COSMA library for communication-optimal matrix multiplication with GPU-aware MPI:

```
cp2k@2024.1 +cuda cuda_arch=80 +cosma ^cosma +gpu_direct
```

COSMA is not available in the uenv described above since it is not a dependency needed by `cp2k@2024.1 +cuda cuda_arch=80`. 

### Spack Environment

To make things clean and reproducible, we use [Spack Environments] do describe what we want to build. To define a [Spack environment] we create the following file in a folder (hereafter referred to as `SPACK_ENV_FOLDER`):

```yaml
spack:
  specs:
  - cp2k@2024.1 +cosma
  packages:
    all:
      prefer:
        - +cuda cuda_arch=80
    cosma:
      require:
        - +gpu_direct
  view: false
  concretizer:
    unify: true
```

`packages:all:prefer` indicates that we want the `+cuda` variant active for all packages that have it. The `require` clause is stronger, and we use it for a specific package, COSMA, to make sure the `+gpu_direct` variant (GPU-aware MPI) is enabled (this is a constraint we want to enforce on the COSMA dependency). 

!!! note
    It is good practice to have a single root [spec] in an environment, and to define constraint on all packages or specific dependencies in the `packages:` field.

### Building

After defining the environment above, we can concretize it:

```bash
spack -e SPACK_ENV_FOLDER concretize -f
```

The result of the concretization will be printed on screen. Packages starting with `[+]` are packages that will be freshly installed in your local [Spack] instance. Packages marked as `[e]` (external) are packages taken directly from the uenv (which we are using as upstream [Spack] instance). You should see many packages marked as `[e]`, which are being re-used from the uenv. This will greatly speed up compilation, since [Spack] will have to build only a small subset of packages.

You can finally build everything in the concretized environment:

```bash
spack -e SPACK_ENV_FOLDER install
```

## Developing with Spack

In addition to wanting to build a different configuration of a package as described above, you might want to build your own software from source. Let's assume we want to develop [CP2K] with the COSMA library as a dependency:

```
cp2k@2024.1 +cuda cuda_arch=80 +cosma ^cosma +gpu_direct
```

We assume again that COSMA is not present in the provided uenv.

### Spack Environment and Building Dependencies

As described above, you can define a [Spack environment] describing the version of the package you want to build and the constraint on the dependencies. After concretizing the environment with

```bash
spack -e SPACK_ENV_FOLDER concretize -f
```

we can tell [Spack] to only install the dependencies, since we want to build the root [spec] manually:

```bash
spack -e SPACK_ENV_FOLDER install --only=dependencies
```

### Building the root spec manually

Finally, we are ready to build the root [spec] manually. With [Spack] you can get a shell within the build environment as follows:

```bash
spack -e SPACK_ENV_FOLDER build-env cp2k -- bash
```

where `cp2k` denotes the root [spec]. Since there is only one such [spec], there is no need to explicitly write out the version nor the variants.

Within the build environment, the software can be built using the provided build system. CP2K uses CMake, therefore we can simply do the following:

```bash
# In CP2K repository root folder

mkdir build && cd build

cmake \
    -GNinja
    -DCP2K_USE_COSMA=ON \
    -DCP2K_USE_ACCEL=CUDA \
    -DCP2K_WITH_GPU=A100 \
    ..

ninja -j 32
```

## Known Limitations

!!! warning
    Swapping the upstream [Spack] instance by loading different uenvs might lead to surprising inconsistencies in the [Spack] database. If this happens, you can uninstall everything from your local [Spack] instance with `spack uninstall --all` and clean up with `spack clean --all`.

[Chaining Spack Installations]: https://spack.readthedocs.io/en/latest/chain.html
[CP2K]: https://eth-cscs.github.io/alps-uenv/uenv-cp2k/
[CP2K Spack package]: https://packages.spack.io/package.html?name=cp2k
[Spack]: https://spack.readthedocs.io/en/latest/
[Spack Basic Usage]: https://spack.readthedocs.io/en/latest/basic_usage.html
[Spack Environments]: https://spack.readthedocs.io/en/latest/environments.html
[Spack environment]: https://spack.readthedocs.io/en/latest/environments.html
[Spack Filesystem Views]: https://spack.readthedocs.io/en/latest/environments.html#filesystem-views
[Spack Getting Started]: https://spack.readthedocs.io/en/latest/getting_started.html
[spec]: https://spack.readthedocs.io/en/latest/basic_usage.html#sec-specs
[Stackinator]: https://eth-cscs.github.io/stackinator/

# Using uenvs as upstream Spack instances

User-environments (uenvs) are built with [Spack] using the [Stackinator] tool. Therefore, a uenv is tightly coupled with [Spack] and can be used as an upstream [Spack] instance (see [Chaining Spack Installations] for more details).

!!! note
    While this guide tries to explain everything step-by-step, it might be difficult to follow without any knowledge of [Spack]. Please have a look at [Spack Basic Usage] for a short introduction to [Spack].

The uenv of a supported application contains all the dependencies to build the software with a particular configuration. In [Spack], such configuration is defined by a [spec] (see [Spack Basic Usage] for more details). Most uenvs already provide modules or [Spack Filesystem Views] which allow to manually build the same configuration. However, it is possible that you want to build or develop an application with a different configuration. To avoid re-building the whole uenv, you can re-use what is already there and build your new configuration using [Spack]. 

This guide explains a _developer workflow_ allowing to either build your own package with [Spack], or use [Spack] to build all the dependencies and provide a build environment for the package.

!!! note
    This guide assumes that you have a local installation of [Spack]. If you don't have [Spack] installed, follow [Spack Getting Started].

!!! tip
    To avoid compatibility issues, try to match the version of your local [Spack] instance with the version of [Spack] of the uenv. You can use the following command to clone the same [Spack] version used by the uenv:
    ```bash
    git clone --filter=tree:0 $(jq -r .spack.repo /user-environment/meta/configure.json)
    git -C spack checkout $(jq -r .spack.commit /user-environment/meta/configure.json)
    ```

!!! warning
    Avoid installing [Spack] on `HOME`. Packages are installed within the `spack/` folder, and you might quickly run out of space. Use `SCRATCH` instead.

!!! danger
    The recommendation to use `SCRATCH` to install your local [Spack] instance(s) might change in the future. Make sure you are aware of our `SCRATCH` cleaning policy. 

## Example: Quantum ESPRESSO

As an example, we will consider [Quantum ESPRESSO] as the application you want to develop. Let's assume that the provided configuration in the official uenv is the following:

```
quantum-espresso@7.3.1 %nvhpc +libxc +cuda cuda_arch=90
```

This [spec] defines a build of [Quantum ESPRESSO] version `7.3.1` using the `nvhpc` compiler. All other dependencies and features are defined by the default values in the [Quantum ESPRESSO Spack package].

## Set uenv as upstream Spack instance

Here we assume the uenv described above is called `quantumespresso/v7.3.1` and it is already deployed. You can therefore pull the `quantumespresso/v7.3.1` image and start the uenv as follows:

```bash
uenv image pull quantumespresso/v7.3.1
uenv start quantumespresso/v7.3.1
```

With the uenv active, you can now tell your local [Spack] instance to use the uenv as an upstream [Spack] instance (see [Chaining Spack Installations] for more details):

```bash
export SPACK_SYSTEM_CONFIG_PATH=/user-environment/config/
```

!!! note
    We assumed here that the uenv is mounted in the standard location `/user-environment/`. If it is mounted in a non-standard location, adjust the previous command accordingly.

## Building your own version 

Let's assume you want to have a version of [Quantum ESPRESSO] with GPU-aware MPI:

```
quantum-espresso@7.3.1 %nvhpc +libxc +cuda cuda_arch=90 +mpigpu
```

This variant of [Quantum ESPRESSO] is not available in the uenv.

### Spack Environment

To make things clean and reproducible, you can use [Spack Environments] to describe what you want to build. To define a [Spack environment] you have to create the following file, named `spack.yaml`, in a folder (hereafter referred to as `SPACK_ENV_FOLDER`):

```yaml
spack:
  specs:
  -  quantum-espresso@7.3.1 %nvhpc +libxc +mpigpu
  packages:
    all:
      prefer:
        - +cuda cuda_arch=90
  view: false
  concretizer:
    unify: true
```

`packages:all:prefer` indicates that you want the `+cuda` variant active for all packages that have it.

!!! note
    It is good practice to have a single root [spec] in an environment, and to define constraint on packages or specific dependencies in the `packages:` field.

!!! tip
    To create an environment you can also use `spack env create SPACK_ENV_FOLDER` and edit the `spack.yaml` file with `spack -e SPACK_ENV_FOLDER config edit`. Alternatively, you can use `spack -e SPACK_ENV_FOLDER add <spec>` to add root specs to the environment and `spack -e config add <config>` to add configutations to the environment. 

!!! example
    An example of creating an environment for building Quantum ESPRESSO:
    ```bash
    spack env create qe-env
    spack -e qe-env  add quantum-espresso%nvhpc +cuda               # Add spec for Quantum ESPRESSO
    spack -e qe-env config add packages:all:prefer:cuda_arch=90     # Add configuration for all packages 
    ```

### Building

After defining the environment above, you can concretize it:

```bash
spack -e SPACK_ENV_FOLDER concretize -f
```

The result of the concretization will be printed on screen. Packages marked with ` - ` are packages that will be freshly installed in your local [Spack] instance. Packages marked as `[^]` (upstream) are packages taken directly from the uenv (which is being used as upstream [Spack] instance). You should see many packages marked as `[^]`, which are being re-used from the uenv. `[e]` (external) are external packages that are already installed in the system (and are defined in the system configuration of the system for which the uenv is built). Finally, packages marked as `[+]` are packages that are already installed in your local [Spack] instances.

Using the uenv as an upstream [Spack] instance will greatly speed up compilation, since [Spack] will have to build only a small subset of packages.

You can finally build everything in the concretized environment:

```bash
spack -e SPACK_ENV_FOLDER install
```

## Developing with Spack (build manually)

In addition to wanting to build a different configuration of a package as described above, you might want to build your own development version of the software from source. Let's assume you want to develop [Quantum ESPRESSO], with GPU-aware MPI:

```
quantum-espresso@7.3.1 %nvhpc +libxc +cuda cuda_arch=90 +gpumpi
```

### Spack Environment and Building Dependencies

As described above, you can define a [Spack environment] describing the version of the package you want to build and the constraints on the dependencies. After concretizing the environment with

```bash
spack -e SPACK_ENV_FOLDER concretize -f
```

you can tell [Spack] to only install the dependencies, since you want to build the root [spec] manually:

```bash
spack -e SPACK_ENV_FOLDER install --only=dependencies
```

### Building the root spec manually

Finally, you are ready to build the root [spec] manually. With [Spack] you can get a shell within the build environment as follows:

```bash
spack -e SPACK_ENV_FOLDER build-env quantum-espresso -- bash
```

where `quantum-espresso` denotes the root [spec]. Since there is only one such [spec], there is no need to explicitly write out the version nor the variants.

Within the build environment, the software can be built using the provided build system. [Quantum ESPRESSO] uses CMake, therefore you can simply do the following:

```bash
mkdir build && cd build

cmake \
    -GNinja
    -DQE_ENABLE_CUDA=ON \
    -DQE_ENABLE_MPI_GPU_AWARE=ON \
    -DQE_ENABLE_LIBXC=ON \
    ..

ninja -j 32
```

## Developing with Spack (build with Spack)

[Spack] already knows how to build [Quantum ESPRESSO] with CMake, therefore you could use [Spack] to build your development version for you.

!!! warning
    Changes to CMake might require changes to the [Quantum ESPRESSO Spack package].

### Spack Environment

You can create a [Spack environment] as suggested above:

```bash
spack env create qe-dev-env
spack -e qe-dev-env add quantum-espresso%nvhpc +libxc +gpumpi
spack -e $SCRATCH/qe-env config add packages:all:prefer:cuda_arch=90
```

In addition to adding [Quantum ESPRESSO] as a root [spec], you have to tell [Spack] where to find the source code (and which version/branch it corresponds to). You can use the following command:

```bash
spack -e qe-dev-env develop -p PATH_TO_QE_SOURCE_CODE quantum-espresso@=develop
```

After concretizing the environment with

```bash
spack -e SPACK_ENV_FOLDER concretize -f
```

you can tell [Spack] to install everything, including Quantum ESPRESSO using the source code in `PATH_TO_QE_SOURCE_CODE`:

```bash
spack -e SPACK_ENV_FOLDER install
```

## Known Limitations

!!! warning
    Swapping the upstream [Spack] instance by loading different uenvs might lead to surprising inconsistencies in the [Spack] database. If this happens, you can uninstall everything from your local [Spack] instance with `spack uninstall --all` and clean up with `spack clean --all`. To avoid this problem, you can also work with multiple local [Spack] instances (one for each uenv).

[Chaining Spack Installations]: https://spack.readthedocs.io/en/latest/chain.html
[Quantum ESPRESSO]: https://www.quantum-espresso.org
[Quantum ESPRESSO Spack package]: https://packages.spack.io/package.html?name=quantum-espresso
[Spack]: https://spack.readthedocs.io/en/latest/
[Spack Basic Usage]: https://spack.readthedocs.io/en/latest/basic_usage.html
[Spack Environments]: https://spack.readthedocs.io/en/latest/environments.html
[Spack environment]: https://spack.readthedocs.io/en/latest/environments.html
[Spack Filesystem Views]: https://spack.readthedocs.io/en/latest/environments.html#filesystem-views
[Spack Getting Started]: https://spack.readthedocs.io/en/latest/getting_started.html
[spec]: https://spack.readthedocs.io/en/latest/basic_usage.html#sec-specs
[Stackinator]: https://eth-cscs.github.io/stackinator/

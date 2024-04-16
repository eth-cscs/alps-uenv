# Application Packaging Tutorial

[Arbor](https://arbor-sim.org/) is scientific software for neuroscience simulation, with features including:

* A C++ library with a Python interface
* Distributed exexcution through MPI
* Multicore simulation
* Support for both NVIDIA and AMD GPUs

Users of Arbor fall into two camps: those who require a version installed, ready to use, on the system; and those who need to build their own copy.

This tutorial walks through configuring and maintaining a uenv recipe and deployment for Arbor that supports the different users, which should cover most of the aspects of deploying your own uenv.

## Requirements

Before starting, we gather requirements for the use cases of the uenv on the system, in order to understand:

* which packages the uenv will provide;
* which interfaces the uenv will provide to those packages.

### Supported workflows

For Arbor we wish to support two workflows:

* *Application*: provide optimised builds of Arbor for users to use directly
* *BYO*: Arbor is under active development, and some users require the ability to build the latest bleeding edge version, or build with a customised configuration.
* *Developer*: Arbor developers who need to implement new features, fix bugs and test on Alps.

Looking at the above, the *BYO* and *Developer* requirements are the same: provide the dependencies required to build Arbor.

### Supported systems

Arbor is well-optimised for both CPU and GPU executation and users of systems with and without accelerators, so we will provide it for the following platforms:

* multicore: `zen2`/`zen3`
* `gh200`

!!! info "supported platforms"

    Supported targets on Alps are currently:

    | target   |
    | -------- |
    | `zen2`   |
    | `zen3`   |
    | `a100`   |
    | `mi200`  |
    | `gh200`  |

    For more information, see the [internal CSCS confluence](https://confluence.cscs.ch/display/VCUE/UENV).
    Also, information about which targets are available on which vClusters, see the [`config.yaml`]().

### Compilers

Arbor is a C++17 libarary that officially supports GCC and Clang, with a Python front end.

For this we choose the following compiler versions:

| target        | compiler   | cuda        | python  |
| ------------- | ---------- | ----------- | ------- |
| `zen2`/`zen3` | `gcc@13.2` | -           | `python@3.11` |
| `gh200`       | `gcc@13.2` | `cuda@12.4` | `python@3.11` |


### Packages

The first step when building an application, use-case or workflow uenv is to determine which specs to add to the list.

If the aim was to provide arbor with cuda and Python support enabled, an `environments.yaml` file that provides a single spec `arbor@0.9 +python` could be sufficient, e.g.:


```yaml title="simple environments.yaml"
arbor:
  compiler:
      - toolchain: gcc
        spec: gcc
  mpi:
      spec: cray-mpich
  unify: true
  specs:
  - arbor@0.9 +python
  variants:
  - +mpi
  - +cuda
  - cuda_arch=90
  views:
    arbor:
      links: root
```

This environment definition will build arbor, with all of its dependencies implicitly concretised by Spack.
Such a simple recipe is sometimes sufficient, however one will often need to provide a more detailed set of specs.
Reasons for more detailed specs include:

* to pin the version of a specific dependency, e.g.:
    - to ensure that the version of a package is not dependent on which version of Spack is used;
    - to a version that is well supported and tested on the target system;
    - to a version that patches a bug on the target system.
* to specialise the spec of a specific depency, e.g.:
    - with non-default variants that support all features on the target system;
    - with non-default variants that give the best performance on the target system;
    - to use a specific compiler when more than one compiler toolchain is used to build packages in an environment.
* to explicitly list all of the dependencies to provide to users in an environment view

The objective for the Arbor uenv is to provide both Arbor and all of the tools and libraries to "build your own" Arbor.
This requires providing all of the libraries and tools required to download the Arbor source code, run CMake, and build in a file system view.

As a starting point, we use the [spack package](https://github.com/spack/spack/blob/develop/var/spack/repos/builtin/packages/arbor/package.py) for Arbor.
From this we derive a list of dependencies:

* direct dependencies like `pugixml`, `fmt` and `pybind11` needed to build Arbor.
* compiler and languages like `python` and `cuda`.

## The Recipe

With requirements in hand, it is now time to write the recipe.

### Config

There are a few simple choices to make when writing the `config.yaml` file:

`name`

:   Keep it simple, we choose `arbor`.

    !!! tip

        Use the same name on all hardware targets, i.e. use a name like `arbor` or `gromacs` instead of `arbor-gpu` or `gromacs-x86`. By doing this users can more easily find your uenv on all vClusters - if they are on a system with an x86 CPU, they can assume that the `arbor` uenv has been built appropriately.

        The uenv CLI tool also allows users to disambiguate which micro-architecture they require, if on a system that provides versions of a uenv built for multiple uarch:

        ```
        uenv image ls --uarch=gh200 arbor
        uenv image ls --uarch=zen2 arbor
        ```

`spack`

:   By default use the most recent version of Spack supported by Stackinator.
    At the time of writing, the most recent version of Spack is `v0.21`, for which it is recommend to use the `releases/v0.21` branch, which receives backports of bug fixes while not changing the API or recipe definitions.

    !!! warning

        The `develop` branch should be avoided for uenv deployed on CSCS clusters unless it is absolutely neccesary.

`mount`

:   Normally application and development uenv go in `/user-environment` and tools that you might want to use alongside a development or application uenv go in `/user-tools` (e.g. a debugger).
    For Arbor, we choose the default `/user-environment` path.

`description`

:   Keep it simple, fit it on one line.


=== "`mc`"

    ```yaml title="config.yaml"
    --8<-- "./recipes/arbor/v0.9/mc/config.yaml"
    ```

=== "`gh200`"

    ```yaml title="config.yaml"
    --8<-- "./recipes/arbor/v0.9/gh200/config.yaml"
    ```

### Compilers

Based on our requirements above, defining compilers is straightforward.

=== "`mc`"

    ```yaml title="compilers.yaml"
    --8<-- "./recipes/arbor/v0.9/mc/compilers.yaml"
    ```

=== "`gh200`"

    ```yaml title="compilers.yaml"
    --8<-- "./recipes/arbor/v0.9/gh200/compilers.yaml"
    ```

### Environments

The environment definitions include the specs that we want to provide to end users, and the selected `cuda` and `python` versions where application.

=== "`mc`"

    ```yaml title="environments.yaml"
    --8<-- "./recipes/arbor/v0.9/mc/environments.yaml"
    ```

=== "`gh200`"

    ```yaml title="environments.yaml"
    --8<-- "./recipes/arbor/v0.9/gh200/environments.yaml"
    ```

    ???+ note "variants"

        Environments on GH200 will typically have the following variants set:

        * `+cuda` sets that variant for all that support it, required for NVIDIA GPU builds.
        * `cuda_arch=90` is required for `gh200` (use `cuda_arch=80` for the `a100` nodes)

!!! tip "views and roots"

    Always use `view:link:roots` if possible to filter which packages are added to views.
    The [default](https://spack.readthedocs.io/en/latest/environments.html#configuration-in-spack-yaml) `all` setting and also the `run` setting can add a lot of packages that were not explicitly in the list of your uenv's specs.

    Packages in the view can lead to conflicts, which can be avoided by only including packages that are strictly required.
    For example, if a view has a common dependency like `libssl` in its `/lib` path, and `LD_LIBRARY_PATH` is set, system CLI tools like `git` can crash because the link against the `libssl` in the uenv at runtime.

### Modules

We add a module file, which controls which modules are [provided by the uenv](https://eth-cscs.github.io/stackinator/recipes/#modules).
This is because some users might want modules, and it doesn't hurt to provide them (this is a weak reason, and we accept that we will be on the hook for supporting them for users who incorporate them into their workflows).

!!! info

    If you don't need to provide modules, set `modules: False` in `config.yaml`.

=== "mc"

    ```yaml title="modules.yaml"
    --8<-- "./recipes/arbor/v0.9/mc/modules.yaml"
    ```

=== "gh200"

    ```yaml title="modules.yaml"
    --8<-- "./recipes/arbor/v0.9/gh200/modules.yaml"
    ```

## Testing

!!! failure

    write reframe tests.

## Deployment

### Configuring the pipeline

The target systems for deploying the Arbor uenv to users are Eiger (`zen2`) and Santis (`gh200`).

To enable the CI/CD pipeline to build and deploy the uenv on these systems, update the [`config.yaml` file in the alps-uenv repository](https://github.com/eth-cscs/alps-uenv/blob/main/config.yaml):

```yaml
uenvs:
  arbor:
    v0.9:
      recipes:
        zen2: v0.9/mc
        gh200: v0.9/gh200
      deploy:
        eiger: [zen2]
        santis: [gh200]
```

!!! tip

    To test that the pipeline yaml is correctly configured before pushing the changes and making a PR, you can run a basic test with the new uenv:

    ```bash
    system=santis uarch=gh200 uenv=arbor:v0.9 ./ci/configure-pipeline
    system=eiger uarch=zen2 uenv=arbor:v0.9 ./ci/configure-pipeline
    ```

    If there are no obvious error messages, you are good to go!

### Running the pipeline

To run the pipeline that will automatically build and test your uenv, first create a PR:

1. Push your changes to a branch (preferably in a fork of the main [alps-uenv](https://github.com/eth-cscs/alps-uenv) repository).
2. Open a PR with your changes.

Once the PR is created, the pipeline has to be triggered for each individual combination of uenv/version/uarch/vCluster by using a specially formatted 

```
cscs-ci run alps;system=eiger;uarch=zen2;uenv=arbor:v0.9
cscs-ci run alps;system=santis;uarch=gh200;uenv=arbor:v0.9
```

### Checking the build

Log onto the target system, e.g. `santis`, and use the `uenv image find --build` command to search for the build.

```
> uenv image find --build arbor
uenv/version:tag                        uarch date       id               size
arbor/v0.9:1250847801                   gh200 2024-04-12 89c9a36f21b496a2 3.6GB
arbor/v0.9:1249535229                   gh200 2024-04-11 0a2d82448ecaafd7 3.6GB
```

!!! info

    The `--build` flag is required with the `find` and `pull` commands to interact with images that have been built by the pipeline, but not yet deployed.

Pick the version that you want to build (if it isn't clear which version to pull, you can find it in the logs of the CI/CD job that built the image).

```bash
# pull the image using its id
uenv image pull --build 89c9a36f21b496a2

# then start the image to test it
uenv image start 89c9a36f21b496a2
```

## Docs

!!! failure

    Write about how to document.

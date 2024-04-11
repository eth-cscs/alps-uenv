# Packaging Tutorial

This tutorial provides an end to end description of configuring and maintaining a uenv recipe and deployment for a representative HPC application.

1. Gathering requirements
2. Writing the recipe
3. Testing
4. Configuring the deployment
5. CI/CD

## Use Case

For this tutorial we will [Arbor](https://arbor-sim.org/) is scientific software for neuroscience simulation, that supports

* A C++ library with a Python interface
* Multicore simulation
* Support for both NVIDIA and AMD GPUs
* Distributed exexcution through MPI


## Requirements

Before starting, we gather requirements for the use cases of the uenv on the system, in order to understand:
* which packages the uenv will provide
* which interfaces the uenv will provide to those packages

### Supported workflows

For Arbor we wish to support two workflows:

* *Application*: provide optimised builds of Arbor for users to use directly
* *BYO*: Arbor is under active development, and some users require the ability to build the latest bleeding edge version themselves.
* *Developer*: Arbor developers use Alps for development. For this we want to provide

Looking at the above, the *BYO* and *Developer* requirements are the same: provide the dependencies required to build Arbor.

### Supported systems

Arbor is well-optimised for both CPU and GPU executation and users of systems with and without accelerators, so we will provide it for the following platforms:

* `a100`
* `gh200`
* multicore: `zen2` and `zen3`

### Compilers

Arbor is a C++17 libarary that officially supports GCC and Clang, with a Python front end.

For this we choose the following compiler versions:

| target    | compiler   | cuda        | python  |
| --------- | ---------- | ----------- | ------- |
| zen2/zen3 | `gcc@13.2` | -           | `python@3.11` |
| gh200     | `gcc@13.2` | `cuda@12.4` | `python@3.11` |


### Packages

The first step when building an application, use-case or workflow uenv is to determine which specs to add to the list.
At a minimum these will be 

If our aim was to provide arbor with cuda and Python support enabled, the following might be sufficient:

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

This environment definition will build arbor, with all of its dependencies concretised and built by Spack.
Such a simple recipe is sometimes sufficient, however we will often want to add to add a more detailed set of specs.
Reasons for more detailed specs include:

* to pin the version of a specific dependency, e.g.:
    - if you want to ensure that the version of a package is not dependent on which version of Spack is used;
    - to a version that we know is well supported and tested on the target system;
    - to a version that patches a bug on the target system.
* to specialise the spec of a specific depency, e.g.:
    - with non-default variants that support all features on the target system;
    - with non-default variants that give the best performance on the target system.
* to explicitly list all of the dependencies that you want to provide to users in an environment view

The objective for this uenv is to provide both Arbor and all of the tools and libraries to "build your own" Arbor.
For that, we need to provide all of the libraries and tools required to download the Arbor source code, run CMake, and build.

As a starting point, we use the [spack package](https://github.com/spack/spack/blob/develop/var/spack/repos/builtin/packages/arbor/package.py) for Arbor.
From this we derive a list of dependencies:

* direct dependencies like `pugixml`, `fmt` and `pybind11` needed to build Arbor.
* compiler and languages like `python` and `cuda`.

## The Recipe

womboat

### config

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

:   By default use the most recent supported version of Spack.
    If the most recent version of Spack is `v0.21`, we recommend using the `releases/v0.21` branch, which receives backports of bug fixes while not changing the API or recipe definitions.

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

### compilers

Based on our requirements, we are using full uenv stacks:

=== "`mc`"

    ```yaml title="compilers.yaml"
    --8<-- "./recipes/arbor/v0.9/mc/compilers.yaml"
    ```

=== "`gh200`"

    ```yaml title="compilers.yaml"
    --8<-- "./recipes/arbor/v0.9/gh200/compilers.yaml"
    ```

## environments

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

!!! warning "views and roots"

    Always use `view:link:roots` if possible to filter which packages are added to views.
    The [default](https://spack.readthedocs.io/en/latest/environments.html#configuration-in-spack-yaml) `all` setting and also the `run` setting can add a lot of packages that were not explicitly in the list of your uenv's specs.

    Including unneccesary packages in the view can lead to conflicts, and should be avoided.
    For example, if a view has a common dependency like `libssl` in its `/lib` path, and `LD_LIBRARY_PATH` is set, system CLI tools like `git` can crash because the link against the `libssl` in the uenv at runtime.


## modules

Our package can 

## Testing

**TODO** 

## Deployment

The target systems for our recipe are Eiger (`zen2`) and Santis (`gh200`).

To enable the CI/CD pipeline to build and deploy the Arbor uenv on these systems, update the [`config.yaml` file in the alps-uenv repository](https://github.com/eth-cscs/alps-uenv/blob/main/config.yaml):

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

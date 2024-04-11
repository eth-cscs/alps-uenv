# Packaging Tutorial

This tutorial provides an end to end description of configuring and maintaining a uenv recipe and deployment for a representative HPC application.

1. Gathering requirements
2. Writing the recipe
3. Testing
4. Configuring the deployment
5. CI/CD

## The Application

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

Looking at the above, the *BYO* and *Developer* requirements are the same: provide the dependencies required to build Arobr.

### Supported systems

Arbor is well-optimised for both CPU and GPU executation and users of systems with and without accelerators, so we will provide it for the following platforms:

* `a100`
* `gh200`
* `zen2`
* `zen3`

### Compilers

Arbor is a C++17 libarary that officially supports GCC and Clang, with a Python front end.

For this we choose the following compiler versions:

| target    | compiler   | cuda        | python  |
| --------- | ---------- | ----------- | ------- |
| zen2/zen3 | `gcc@13.2` | -           | `python@3.11` |
| gh200     | `gcc@13.2` | `cuda@12.4` | `python@3.11` |
| a100      | `gcc@11.8` | `cuda@11.8` | `python@3.11` |

=== "`zen2`/`zen3`"

    ```yaml
    foo: bar
    ```

=== "`gh200`"

    ```yaml
    foo: bar
    ```

???+ note

    Currently two compiler toolchains are available: `gcc` and `nvhpc`.
    The `nvhpc` toolchain is rife with compiler bugs for C and C++, that makes building a full software stack challenging.
    As a rule we only use `nvhpc` when neccesarily, which typically means for Fortran applications that need OpenACC on NVIDIA GPU or compatibility with the PGI compiler toolchain.
    In such cases, the `nvhpc` compiler toolchains are used together, with gcc used to build as many C/C++ dependencies as possible.

### Packages

The first step when building an application, use-case or workflow uenv is to determine which specs to add to the list.
At a minimum these will be 

Arbor has a Spack package definition that we can use to understand the basic requirements.

If our aim was to only support the aplication workflow, the following might be sufficient:

```yaml
specs:
  - arbor +cuda +python +mpi
  - python
```


We will use the [development version](https://github.com/arbor-sim/arbor/blob/master/spack/package.py)



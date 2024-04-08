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

Arbor is well-optimised for both CPU and GPU executation and users of systems with and without accelerators, so we will provide it for the following platforms

* a100
* gh200
* zen2/zen3

### Packages

Arbor has a Spack package definition that we can use to understand the basic requirements.

If our aim was to only support the aplication workflow, the following might be sufficient:

```yaml
specs:
  - arbor +cuda +python +mpi
  - python
```



We will use the [development version](https://github.com/arbor-sim/arbor/blob/master/spack/package.py)

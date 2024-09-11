# ReFrame Testing Tutorial

When ReFrame tests are enabled for a uenv, they are automatically run:

* in the CI/CD pipeline after the image has been built;
* in daily/weekly testing of individual vClusters;
* and when upgrading and updating vClusters.


the basic set of steps

1. Create or port tests in the [eth-cscs/cscs-reframe-tests]
2. Make a pull request to have the tests added to the `alps` branch of the 
3. Add a `extras/reframe.yaml` file to your uenv recipe.
4. Make a pull request to merge with the alps-uenv repository.

## How uenv ReFrame testing works

CSCS maintains a set of ReFrame tests in the CSCS ReFrame tests repository [eth-cscs/alps-uenv].
These tests cover a very wide range of features, including application tests, login node health and Slurm, and can be run on any vCluster on Alps.

Setting up tests for your uenv requires making changes to two repositories:

* [eth-cscs/alps-uenv] adding meta data to the uenv that can be used by ReFrame to:
    * configure a uenv so that it is ready to run tests;
    * choose which tests from the test suite are used to test the uenv.
* [eth-cscs/cscs-reframe-tests] adding and updating tests in the Reframe repository that are relevant to the uenv.
    * might not be necessary if the tests already exist.

### uenv recipe meta data

To enable ReFrame tests in your uenv, and yaml file `extra/reframe.yaml` should be added to the recipe.

Below is an example `reframe.yaml` file:

```yaml title="extra/reframe.yaml for testing a single environment provided by a uenv"
develop:
  features:
    - cuda
    - mpi
    - arbor-dev
  cc: mpicc
  cxx: mpic++
  ftn: mpifort
  views:
    - develop
```

This configuration defines a single _environment_ named `develop`, which corresponds a [ReFrame environment], with some additions.

* `features`: a list of ReFrame features that are provided by the environment.
    * used to decide which tests will be run against the uenv.
    * in this case the uenv provides:
        * `cuda`: expect tests that compile and test NVIDIA gpu aware problems.
        * `mpi`: expect basic MPI tests that compile and validate MPI to be run. When combined with `cuda` above, tests for GPU-aware MPI will be run.
        * `arbor-dev`: a specific feature that specifies that _the environment provides everything required to build and run arbor_.
* `cc`, `cxx`, `ftn`: define the compiler aliases
    * see the [ReFrame environment]s documentation.
* `views`: **(optional)** a list of views to load.
    * in this case `develop` view is to be loaded.

Uenv can provide multiple environments, for different use cases.
The most common example is a uenv that provides two views: one that provides an application, and another that provides the tools used to build the application. Another example is the `modules` and `spack` views, that expose a module interface or useful configuration for using Spack with the uenv.

Similarly, it is possible to create multiple environments to test.
The example below defines two environments that provide the same features, i.e. the same tests will be run on each.
The first example is the one above, and the second sets up an equivalent environment using modules.
This would be useful for a uenv that has some users who insist on using modules to set up their build enviroment.

```yaml title="extra/reframe.yaml for multiple environments to test"
develop:
  features:
    - cuda
    - mpi
    - arbor-dev
  cc: mpicc
  cxx: mpic++
  ftn: mpifort
  views:
    - develop
modules:
  features:
    - cuda
    - mpi
    - arbor-dev
  cc: mpicc
  cxx: mpic++
  ftn: mpifort
  views:
    - modules
  activation:
    - module load cuda cray-mpich cmake ninja fmt
```

!!! question "What is an environment, anyway?"

    What is the difference between using `module load`, activating a python venv, loading a spack environment, or a uenv view?

    Nothing!

    They all do the same thing - set environment variables.

    The main variables that change the behavior of the system are `PATH` and `LD_LIBRARY_PATH`, though there are many others like `PKG_CONFIG_PATH`, `CUDA_HOME`, `MODULEPATH` etc that will have more subtle effects on configuring and building software.

    When we configure an environment for running tests, we are specifying the commands that will **modify and set environment variables** such that the tests can run. For example, a view or module might be loaded to make the executable of a scientific code be in `PATH`, or to add tools like `cmake`, `nvcc` and `gcc` to `PATH` so that we can run a test that builds an application.

```yaml
develop:
  features:
    - cuda
    - mpi
    - arbor-dev
  cc: mpicc
  cxx: mpic++
  ftn: mpifort
  views:
    - develop
modules:
  features:
    - cuda
    - mpi
    - arbor-dev
    - python
  cc: mpicc
  cxx: mpic++
  ftn: mpifort
  views:
    - modules
  activation:
  - module load cmake ninja cuda gcc cray-mpich python
```

## Creating uenv tests

The final objective for adding tests to a uenv is to have:

1. a uenv deployed with an `meta/extra/reframe.yaml` file;
2. and tests in the [eth-cscs/cscs-reframe-tests] repository

In this second half of the tutorial, a workflow for doing this that minimises the amount of time spent waiting in job and ci/cd queues is provided.

* a working uenv squashfs image with corresponding meta data.
* a list of which tests you want to run against the uenv (some of which you have yet to write).

## Step 1: create a reframe.yaml file

```bash
# pull the image that you want to start developing tests for
$ uenv image pull cp2k/24.7:v1

# get the meta data path
$ meta=$(uenv image inspect cp2k/2024.2:v1 --format={meta})

# check the path - your location will be different
$ echo ${meta}

# create the file
$ mkdir -p ${meta}/extra
$ vim ${meta}/extra/reframe.yaml
```

The `meta` path is the meta data for the uenv for the image.

??? note "why create reframe.yaml in this location?"

    We inject the `reframe.yaml` file into the meta data in the uenv repo to create a "development environment", where it can be modified while developing the tests in an interactive shell.

    The `reframe.yaml` file will be added to the recipe later, once it is time to start testing in a ci/cd pipeline.


## Step 2: set up the CSCS reframe tests




```bash
# download the reframe tests
$ git clone -b alps git@github.com:eth-cscs/cscs-reframe-tests.git
$ cd cscs-reframe-tests

# start a branch for developing the tests
git checkout -b arbor
```

!!! tip

    Always create your working branch off of the `alps` branch.
    The `alps` branch is used for tests run on Alps vClusters. It will become the main branch, once Piz Daint is decommisioned.

```
# create a path for the checks
mkdir checks/apps/arbor
cd checks/apps/arbor
```

## Adding tests to a uenv

## Running tests

The ReFrame tests are run automatically in the CI/CD pipeline, in the `test` stage, directly after the `build` stage.

[eth-cscs/alps-uenv]: https://github.com/eth-cscs/alps-uenv
[eth-cscs/cscs-reframe-tests]: https://github.com/eth-cscs/cscs-reframe-tests
[ReFrame environment]: https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#environment-features-and-extras

# ReFrame Testing Tutorial

When [ReFrame] tests are enabled for a uenv, they are automatically run:

* in the CI/CD pipeline after the image has been built;
* in daily/weekly testing of individual vClusters;
* and when upgrading and updating vClusters.

This page is a tutorial that will guide you through the process of enabling testing for your uenv, and on writing portable tests that will run on any uenv-enabled system on [Alps].

!!! info

    Currently this tutorial shows how to create and run tests for a uenv image that has already been created.

    TODO:

      * Describe how to add the test to the recipe and view the test results in the CI/CD pipeline

## How uenv ReFrame testing works

CSCS maintains a set of [ReFrame] tests in the CSCS ReFrame tests repository [eth-cscs/cscs-reframe-tests].
These tests cover a very wide range of features, including application tests, login node health and Slurm, and can be run on any vCluster on Alps.

!!! info

    When running this test suite with a uenv, only the subset of the test suite that is relevant for the uenv will be run.

Setting up tests for a uenv requires making changes to two repositories:

* [eth-cscs/alps-uenv] **adding metadata to the uenv** to be used by ReFrame to:
    * load the uenv and configure the environment so that it is ready to run tests;
    * and, choose which tests from the test suite are used to test the uenv.
* [eth-cscs/cscs-reframe-tests] **updating and adding tests** in the that are relevant to the uenv.
    * might not be necessary if the tests already exist.

### uenv recipe meta data

To enable ReFrame tests in your uenv, a yaml file `extra/reframe.yaml` should be added to the recipe.

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
        * `cuda`: expect tests that compile and test NVIDIA GPU aware problems.
        * `mpi`: expect basic MPI tests that compile and validate MPI to be run. When combined with `cuda` above, tests for GPU-aware MPI will be run.
        * `arbor-dev`: a specific feature that specifies that _the environment provides everything required to build and run arbor_.
* `cc`, `cxx`, `ftn`: define the compiler aliases
    * see the [ReFrame environment]s documentation.
* `views`: **(optional)** a list of views to load.
    * in this case `develop` view is to be loaded.

A uenv can provide multiple views, for different use cases.
The most common example is a uenv that provides two views: one that provides an application, and another that provides the tools used to build the application. Another example is the `modules` and `spack` views, that expose a module interface or useful configuration for using Spack with the uenv.

Similarly, it is possible to create multiple environments to test.
The example below defines two environments that provide the same features, i.e. the same tests will be run on each.
The first example is the one above, and the second sets up an equivalent environment using modules.
This would be useful for a uenv that has some users who insist on using modules to set up their build environment.

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

!!! info

    The `modules` environment uses an additional `activation` field, which is a series of commands
    to run in the shell before running the tests. In this case, modules provided by the uenv are loaded.

!!! question "What is an environment?"

    What is the difference between using `module load`, activating a python venv, loading a Spack environment, or a uenv view?

    Nothing!

    They all do the same thing - set environment variables.

    The main variables that change the behavior of the system are `PATH` and `LD_LIBRARY_PATH`, though there are many others like `PKG_CONFIG_PATH`, `CUDA_HOME`, `MODULEPATH` etc that will have more subtle effects on configuring and building software.

    Configuring an environment for running tests requires specifying the commands that will **modify and set environment variables** such that the tests can run. For example, a view or module might be loaded to make the executable of a scientific code be in `PATH`, or to add tools like `cmake`, `nvcc` and `gcc` to `PATH` so that we can run a test that builds an application.

## Creating uenv tests

The final objective for adding tests to a uenv is to have:

1. a uenv deployed with an `extra/reframe.yaml` file;
2. and tests in the [eth-cscs/cscs-reframe-tests] repository

In this second half of the tutorial, a workflow for doing this that minimises the amount of time spent
waiting in job and CI/CD queues is provided.
Before starting, you will need the following:

* a working uenv squashfs image with corresponding meta data path;
* and a list of which tests you want to run against the uenv (some of which you have yet to write).

### Step 1: create a reframe.yaml file

```bash
# pull the image that you want to start developing tests for, e.g.:
$ uenv image pull cp2k/2024.2:v1

# get the meta data path
$ meta=$(uenv image inspect cp2k/2024.2:v1 --format={meta})

# check the path - your location will be different
$ echo ${meta}

# create the reframe meta data file
$ mkdir -p ${meta}/extra
$ vim ${meta}/extra/reframe.yaml
```

The `meta` path is the metadata for the uenv for the image.

??? note "why create reframe.yaml in this location?"

    We inject the `reframe.yaml` file into the meta data in the uenv repo to create a "development environment", where it can be modified while developing the tests in an interactive shell.

    The `reframe.yaml` file will be added to the recipe later, once it is time to start testing in a CI/CD pipeline.


### Step 2: set up the CSCS reframe tests

The next step is to check out and setup ReFrame and the CSCS ReFrame test suite.

It might be a good idea to create a path for this work, and cloning the ReFrame and CSCS test suite repos as sub-directories.

### Set up ReFrame

The first step is to download and set up ReFrame:

* clone from [ReFrame GitHub repository](https://github.com/reframe-hpc/reframe)
* run the bootstrap process that installs ReFrame's dependencies;
* then add reframe to `PATH`.

```bash
# clone from repo
$ git clone git@github.com:reframe-hpc/reframe.git

# run bootstrap process (only needs to be done once)
$ cd reframe
$ ./bootstrap.sh

# add to PATH and verify that everything works
$ export PATH=$PWD/bin:$PATH
$ reframe --version
```

### Set up the ReFrame tests

The next step is to clone the CSCS test suite, and create a new branch where we will make any changes required to test our uenv.

```bash
# download the reframe tests
$ git clone -b alps git@github.com:eth-cscs/cscs-reframe-tests.git
$ cd cscs-reframe-tests

# start a branch for developing the tests (choose your own appropriate name)
git switch -c uenv-arbor
```

!!! tip

    Always create your working branch off of the `alps` branch.
    The `alps` branch is used for tests run on Alps vClusters. It will become the main branch, once Piz Daint is decommisioned.

## Adding/updating tests to a uenv

Now everything is in place to implement the tests for your uenv, which will involve one or two of the following:

1. add some new tests;
2. or, updating / porting existing tests that were written for the CPE+EasyBuild builds on Daint XC or Eiger.

There are no existing tests for Arbor, so let's start by creating a path for the tests we will write:

```
# create a path for the checks
mkdir checks/apps/arbor
cd checks/apps/arbor
```

!!! note

    If there are existing tests, start editing the existing tests directly, or create a new test in that path.

In this tutorial we will write tests that:

1. build Arbor, including unit tests and example miniapps
2. run Arbor's unit tests
3. run a benchmark with a single MPI rank on one GH200 GPU
3. run a benchmark with 4 ranks and 4 GPUs on a GH200 node.

[Link to the tests](https://github.com/eth-cscs/cscs-reframe-tests/tree/alps/checks/apps/arbor).

!!! note

    These tests use the packages and tools in the uenv (CMake, cray-mpich, Python, cuda, etc) to build Arbor, then as runtime dependencies for running the Arbor tests.

    If your uenv provides a pre-built application, you can skip building and use the executable directly to run validation and benchmark tests.

Here is a link to the tests for Arbor: [`checks/apps/arbor/arbor-dev.py`](https://github.com/eth-cscs/cscs-reframe-tests/blob/alps/checks/apps/arbor/arbor-dev.py).

The modules `import`ed at the top of the file will depend on the ReFrame features used for the tests.
The `uenv` module is implemented in [`config/utilities/uenv.py`](https://github.com/eth-cscs/cscs-reframe-tests/blob/alps/config/utilities/uenv.py):

```python
import uenv
```

It provides the `uenv.uarch()` function, that will be used to determine the uenv
uarch (`gh200`, `a100`, `zen2`, etc.) of the system where tests are running.
We will see it in action below.

### Test: building the software

Building is handled by a test, in this case called [`arbor_build`](https://github.com/eth-cscs/cscs-reframe-tests/blob/alps/checks/apps/arbor/arbor-dev.py#L47-L93), that derives from `rfm.CompileOnlyRegressionTest`.

!!! info

    Points of interest are annotated in the code below with :material-plus-circle: symbols, click on them to expand.

``` { .python .annotate }
class arbor_build(rfm.CompileOnlyRegressionTest):
    descr = 'Build Arbor'
    valid_systems = ['*']
    valid_prog_environs = ['+arbor-dev'] #(1)
    build_system = 'CMake'
    sourcesdir = None
    maintainers = ['bcumming']
    arbor_sources = fixture(arbor_download, scope='session') #(2)
    build_locally = False #(3)

    @run_before('compile')
    def prepare_build(self):
        self.uarch = uenv.uarch(self.current_partition) #(4)
        self.build_system.builddir = os.path.join(self.stagedir, 'build')
        tarball = f'v{self.arbor_sources.version}.tar.gz'

        tarsource = os.path.join(self.arbor_sources.stagedir, tarball)
        self.prebuild_cmds = [
            f'tar --strip-components=1 -xzf {tarsource} -C {self.stagedir}'
        ]

        self.build_system.config_opts = [
            '-DARB_WITH_MPI=on',
            '-DARB_WITH_PYTHON=on',
        ]
        # set architecture-specific flags
        if self.uarch == 'gh200': #(5)
            self.build_system.config_opts += [
                '-DCMAKE_CUDA_ARCHITECTURES=90',
                '-DARB_GPU=cuda',
            ]
        elif self.uarch == 'a100':
            self.build_system.config_opts += [
                '-DCMAKE_CUDA_ARCHITECTURES=80',
                '-DARB_GPU=cuda',
                '-DARB_VECTORIZE=on'
            ]
        elif self.uarch == 'zen2':
            self.build_system.config_opts += ['-DARB_VECTORIZE=on']

        self.build_system.max_concurrency = 64

        self.build_system.make_opts = ['pyarb', 'examples', 'unit']
```

1.  Restrict this test to only run in environments that provide the `arbor-dev` feature.
    This can be a list of environments, e.g. `['+arbor-dev+cuda', '+python']` would run the test in environments that provide both `arbor-dev` and `cuda`, or environments that provide `python`.
2.  `arbor_download` is a [ReFrame fixture](https://reframe-hpc.readthedocs.io/en/v4.5.0/tutorial_fixtures.html), that handles downloading the source for Arbor.
3.  The build stage is performed on a compute node using a sbatch job.
    Required so that the environment is configured properly, by adding the
    correct flags to the script:
    ```
    #SBATCH --uenv=...
    #SBATCH --view=...
    ```
4. Determine the uarch of the nodes in the current partition, which will be a string like `"gh200"`, `"a100"`, "`zen2`", etc.
5. Use the uarch to set node-specific flags.


!!! note

    At no point do we mention specific cluster names or partitions.
    This is different from how tests were written for Daint and Eiger in the past, where the test would
    include explicit mentions of systems:

    ```python
    if self.current_system.name in ['daint', 'dom']:
      self.num_tasks = 576
      self.num_tasks_per_node = 36
    ```

    The new approach of parameterising over uarch means that the test can be configured for _any_ vCluster with gh200 nodes.

### Test: run the unit tests

The C++ Arbor library provides GoogleTest unit tests that are bundled in a single executable `unit`.
The tests are not MPI enabled, and take less than 30 seconds to run 1000 individual tests.
As such, they are a good quick test!

``` { .python .annotate }
@rfm.simple_test #(1)
class arbor_unit(rfm.RunOnlyRegressionTest):
    descr = 'Run the arbor unit tests'
    valid_systems = ['*']
    valid_prog_environs = ['+arbor-dev']
    time_limit = '5m' #(2)
    maintainers = ['bcumming']
    arbor_build = fixture(arbor_build, scope='environment') #(3)

    @run_before('run')
    def prepare_run(self):
        self.executable = os.path.join(self.arbor_build.stagedir,
                                       'build', 'bin', 'unit')
        self.executable_opts = []

    @sanity_function
    def validate_test(self):
        return sn.assert_found(r'PASSED', self.stdout) #(4)
```

1.  This is the first time that we have added an annotation to a test.
    This is a "leaf" in our set of test dependencies, run after the download
    and build stages that are its dependencies have run.
2.  The unit tests run quickly - so set a short time limit for higher priority queuing
3.  The `arbor_build` stage has to be run before this test, to build the unit tests.
4.  Just check that the tests passed - performance checks are implemented elsewhere

### Test: single GPU benchmark

Use the `miniring` benchmark provided by Arbor to check both correctness and performance.

The tests will run the `busyring` test in two configurations on a single GPU: `small` and `medium` in this test.
A separate test (see later) will also run the `medium` module on 4 GPUs.

To test for performance, target performance values need to be provided.
We create reference target values, in a dictionary outside the test class, for the following reasons:

* To ensure that the tests can be run across _any_ `cluster:partition` with supported uarch.
* Splitting the reference data out in this way makes it simpler to add feaures like reading performance targets from file, and adding new targets for a new uarch without touching the test itself.

``` { .python .annotate }
arbor_references = {
    'gh200': { #(1)
        'serial': {
            'small': {
                'time_run':  (9.25, -0.1, 0.1, 's'), # (2)
            },
            'medium': {
                'time_run':  (35.0, -0.05, 0.05, 's'),
            }
        },
        'distributed': {
            'medium': {
                'time_run':  (9.2, -0.05, 0.05, 's'),
            }
        },
    }
}
```

1. Currently, we only have Arbor performance targets for `gh200`, fields for `zen2` would be added for Eiger testing.
2. These are labelled reference targets. A link will be added when it is found in ReFrame's "documentation".

The test itself:

``` { .python .annotate }
@rfm.simple_test
class arbor_busyring(rfm.RunOnlyRegressionTest):
    """
    run the arbor busyring example in small and medium model configurations
    """
    descr = 'arbor busyring model'
    valid_systems = ['*']
    valid_prog_environs = ['+arbor-dev'] #(1)
    maintainers = ['bcumming']
    model_size = parameter(['small', 'medium']) #(2)

    arbor_build = fixture(arbor_build, scope='environment') #(3)

    @run_before('run')
    def prepare_run(self):
        self.executable = os.path.join(self.arbor_build.stagedir,
                                       'build', 'bin', 'busyring')
        self.executable_opts = [f'busyring-input-{self.model_size}.json']

        self.uarch = uenv.uarch(self.current_partition) #(4)
        if (self.uarch is not None) and (self.uarch in arbor_references):
            self.reference = {
                self.current_partition.fullname:
                    arbor_references[self.uarch]['serial'][self.model_size]
            }

    @sanity_function
    def validate_test(self):
        # if the meters are printed, the simulation ran to completion
        return sn.assert_found(r'meter-total', self.stdout)

    @performance_function('s')
    def time_run(self):
        return sn.extractsingle(r'model-run\s+(\S+)', self.stdout, 1, float)
```

1. Only run in environments that provide `arbor-dev`
2. The model is parameterised on model size. In practice this means that ReFrame will run
   the test twice, once for each parameter.
   The value of the parameter can be accessed as `self.model_size`, see the `prepare_run` method below.
3. Requires the build stage.
4. Instead of explicitly listing performance targets for all possible
   `system:partition` combinations, set the reference targets to those for the uarch _of the current partition_.
   In other words - the performance target is set dynamically based on the architecture of the node,
   instead of being hard coded using if-else statements in the test itself.

     * `self.uarch` is one of the alps arch: `"gh200"`, `"zen2"`, `"a100"`, ... etc., or `None`
     * `self.current_partition.fullname` is the `vcluster:partition` string, for example `"daint:normal"` or `"todi:debug"`.

!!! note

    The test will still run, and the `time_run` results will still be reported, when `arbor_references`
    does not provide values for the current uarch.
    However, in such cases, no comparison is made and the test will pass.

### Test: MPI tests

``` { .python .annotate }
slurm_config = { #(1)
    'gh200': {"ranks": 4, "cores": 64, "gpu": True},
    'zen2':  {"ranks": 2, "cores": 64, "gpu": False},
}

@rfm.simple_test
class arbor_busyring_mpi(arbor_busyring): #(2)
    """
    adapt the busyring test to check paralle MPI execution
    """

    descr = 'arbor busyring model MPI on a single node'
    model_size = parameter(['medium']) # (3)

    @run_before('run')
    def prepare_run(self):
        self.uarch = uenv.uarch(self.current_partition)
        self.executable = os.path.join(self.arbor_build.stagedir,
                                       'build', 'bin', 'busyring')
        self.executable_opts = [f'busyring-input-{self.model_size}.json']

        self.num_tasks = slurm_config[self.uarch]["ranks"] # (4)
        self.num_cpus_per_task = slurm_config[self.uarch]["cores"]
        if slurm_config[self.uarch]["gpu"]:
            self.job.options = ['--gpus-per-task=1']

        if (self.uarch is not None) and (self.uarch in arbor_references): 
            self.reference = { # (5)
                self.current_partition.fullname:
                    arbor_references[self.uarch]['distributed'][self.model_size]
            }
```

1.  Store the slurm configuration outside the test, like we did for the performance targets
2.  This test shares a lot with the basic `arbor_busyring` test - so inherit.
    This might be code stink in this case, but it is useful for showing how to use inheritance to refine tests.
3.  Reduce the model size parameter to a single option `medium` (this overwrites the inherited parameter)
4.  Parameterise the Slurm configuration (the `num_tasks`, `num_cpus_per_task` etc magic variables) on uarch.
4.  Parameterise the performance target on uarch.

## Running tests

To run the tests, the first thing to do is set an environment variable that will be used by the
test suite to configure the environment.

```bash
$ export UENV=arbor/v0.9:v1
```

!!! warning

    Currently only a uenv label can be used, i.e. the image must have already been built and pulled
    into a local uenv repository, that is via `uenv image pull` or `uenv image pull --build`.

    We will update this feature to allow you to provide the path of the squashfs image.
    It will be a hard requirement that the meta data path will be in the same path
    as the `store.squashfs` file.

!!! warning
    If the `UENV` variable is not set proprely, the `reframe.yaml` file can't be found and you will see an error:
    ```
    ERROR: failed to load configuration: problem loading the metadata from 'extra/reframe.yaml' 
    ```

To run the tests use the following commands:

```bash
# run the tests
$ reframe -C cscs-reframe-tests/config/cscs.py \
  -c cscs-reframe-tests/checks/apps/arbor/ --keep-stage-files \
  -r

# perform a dry run of tests
$ reframe -C cscs-reframe-tests/config/cscs.py \
  -c cscs-reframe-tests/checks/apps/arbor/ --keep-stage-files \
  --dry-run
```

* `-C`: the system configuration, here provided by the CSCS test suite
* `-c <path> -r`: the path containing checks to run. The `-r` flag will search recursively for tests in sub-directories
    * in this case, only consider the arbor tests.
    * `-c cscs-reframe-tests/checks` would search through all tests for tests that
      are compatible with the features provided by the environments in the `extra/reframe.yaml` file.
* `--keep-stage-files`: this will keep all of the intermediate scripts and configuration
    * stored in the `stage` sub-directory of the current path.
    * very useful for debugging problems with our tests.
* `--dry-run`: generate all the stage files and scripts without running the tests.

!!! tip

    Use the `--dry-run` first, to inspect the generated job scripts and that there are no issues
    in the code. Once everything looks good, remove the flag to run the tests (which would take longer).

!!! tip

    Look in the `stage` path that is created in the path where you called reframe for all
    of the job scripts, build files, and results.

!!! tip
    If ReFrame tests fail because of `ReqNodesNotAvail` and you think it is a fluke, try setting
    `RFM_IGNORE_REQNODENOTAVAIL=y`.

[eth-cscs/alps-uenv]: https://github.com/eth-cscs/alps-uenv
[eth-cscs/cscs-reframe-tests]: https://github.com/eth-cscs/cscs-reframe-tests
[ReFrame environment]: https://reframe-hpc.readthedocs.io/en/stable/tutorial.html#environment-features-and-extras
[ReFrame]: https://reframe-hpc.readthedocs.io/en/stable/
[Alps]: https://www.cscs.ch/computers/alps

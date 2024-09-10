# Using uenv to build and run applications on Alps

## logging in

Once you have set up your ssh token, an easy way to simplify login in is by updating your `~/.ssh/config`:

```console
> cat ~/.ssh/config
Host ela
    HostName ela.cscs.ch
    ForwardAgent yes
    User bcumming

Host daint.alps
    HostName daint-ln001.cscs.ch
    ProxyJump ela
    User bcumming
```

Then log into one of the systems using the alias defined in the config file:
```console
ssh todi
ssh daint.alps
```

## setting up for the first time

First, check that uenv has been installed on the system:
```console
uenv --version
uenv status
```

Before using uenv, a repository (repo) for storing downloaded (pulled) needs to be created.

e.g. try the following command that lists the downloaded uenv:
```console
uenv image ls
```

Create a repo in the default location
```console
# get help on the repo command
uenv repo --help

# find the status of the default repo
uenv repo status

# create the new repo
uenv repo create
find $SCRATCH/.uenv-images
```

## finding and pulling images

To search for the uenv that are provided by CSCS, use the `uenv image find` command when logged in:

```console
uenv image find                 # all uenv on the current system
uenv image find cp2k            # all cp2k images on the current system
uenv image find cp2k/2024.2     # refine the search
uenv image find cp2k/2024.2:v1  # refine the search
uenv image find --system=eiger  # choose the system
uenv iamge find --uarch=gh200   # choose the uarch
```

To download an image, use the `uenv image pull` command
```console
uenv image pull editors
```

There might be more than one uenv that matches the description. If so, be more specific:

* use the full disambiguated name
* use the image hash or id
* specify the uarch

```console
uenv image pull editors/24.7:v1
uenv image pull 95fc886e35a3b27f
uenv image pull editors --system=daint
```

Look at the repository, to see what has been downloaded:
```console
find $SCRATCH/.uenv-images
```

Let's also pull another couple of uenv

```console
uenv image pull prgenv-gnu/24.7:v3
```

## inspecting uenv

Let's say we have pulled some some uenv, e.g.:
```console
> uenv image ls
uenv/version:tag                        uarch date       id               size
prgenv-gnu/24.7:v3                      gh200 2024-08-23 b50ca0d101456970 3.8GB
editors/24.7:v1                         gh200 2024-09-01 95fc886e35a3b27f 1.2GB
arbor/v0.9:1435230711                   gh200 2024-09-01 41fbf21853e82969 3.6GB
```

To get more information about a uenv, use the `uenv image inspect` command
```console
> uenv image inspect prgenv-gnu
```

The output can be formatted using Jinja2 templates, (useful for automated workflows):
```console
> uenv image inspect prgenv-gnu --format={sqfs}
```
For example, print all uenv with their views:
```console
for id in $(uenv image ls --no-header | awk '{print $4}');
do
    meta=$(uenv image inspect --format '{meta}' $id)/env.json;
    echo "$id : $(jq -j '.views | keys | join(" ")' $meta)";
done;
```

You can see a full list of format options:
```console
uenv image inspect --help
```

## using uenv

### starting a uenv

start running a uenv

```console
uenv start prgenv-gnu
```

What happened? The squashfs image was mounted:

```console
findmnt --mountpoint /user-environment
ls /user-environmment
```

uenv provides a command for checking whether a uenv is running:
```console
> uenv status
/user-environment:prgenv-gnu
  GNU Compiler toolchain with cray-mpich, Python, CMake and other development tools.
  views:
    default
    modules: activate modules
    spack: configure spack upstream
```

???+ info

    The `uenv start` and `uenv run` commands (see below) create a new process and mount the image so that that process is the only one that can read the mounted image.
    This isolates different users and login sessions on the same compute/login node - different users can have their own uenv mounted at the same location without affecting one another.

The software has been mounted, but it is not yet available in the environment:
```console
gcc --version
which gcc
cmake --version
which cmake
python3 --version
which python3
```
Python 3.6 is the default provided by SLES - not good enough for the discerning HPC user!

On HPC systems, software is usually "loaded" using modules. The software packages are installed in subdirectories, e.g. `netcdf` provided by CPE:
```
/opt/cray/pe/netcdf/4.9.0.9/gnu/12.3
/opt/cray/pe/netcdf/4.9.0.9/crayclang/17.0
```
Each of these contains a `bin`, `include`, and `lib` paths.

`module load netcdf` will set environment variables `PATH`, `LD_LIBRARY_PATH`, etc - making the software available.

### uenv views modify the environment

```
# leave the previous uenv session
exit

# start with a view activated
uenv start prgenv-gnu --view=default

# now the software is available
cmake --version
which cmake
python3 --version
which python3
gcc --version
which gcc
nvcc --version
which nvcc
```

Let's have a closer look at `/user-environment/env/default/`

### Can I mix and use multipe uenv at the same time?

A difference between uenv and modules are that setting up the environment is more "declarative" than "imperative":

* the images to mount and views to start are specified at the start of a session
* after they are set, they can't change
    * if you use the `modules` view, it is possible to `load`, `swap`, `purge` etc as in the days of yore.

It is not possible to run "uenv inside uenv"

* the first reason is security
* each uenv has a fixed mount point - only one image can be mounted at a location

This can be frustrating compared to using modules, when experimenting and testing on the command line:

* swapping uenv, views, etc requires going back to the start
* when using modules, one can continuously load, unload, swap, purge modules while interacting with the shell.

We might also be used to putting code like this in `.bashrc` to set up a "default" environment:
```console
module swap PrgEnv-cray PrgEnv-gnu
module swap gcc/12.3.0 module load cudatoolkit
```

An equivalent approach with `uenv` is not possible
```console
# the following starts a new shell
# ... and once loaded, we can't load a different shell
uenv start my-default-environment --view=work
```

The benefit of this approach is that reproducing a working environment is simpler:

* `uenv start cp2k/2024.2,editors --view=cp2k:develop,ed` describes the environment

This will hopefully reduce the frequency of one of the main challenges when reproducing issues affecting our users

* long-forgotten module commands in bashrc
* "this worked yesterday when this combination of modules was loaded in this order"

???+ note

    Please report pain points in your workflow.

### It is possible to use more than one uenv simultaneously

It is possible to mount more than one uenv in the same session, so long as they are both configured "up front" when the session is started.

Examples for this use case include:

* using a profiler or debugger uenv alongside a programming environment or application uenv
* mounting useful utilities (e.g. editors) alongside a programming environment.

```console
# start two uenv in the same session
uenv start prgenv-gnu editors

# provide custom mount points
uenv start prgenv-gnu:/user-tools editors:/user-environment
uenv status

# start two uenv in the same session with views
uenv start prgenv-gnu editors --view=prgenv-gnu:modules,ed

# disambiguate the view name
uenv start prgenv-gnu editors --view=prgenv-gnu:modules,ed
```

### why are there both `uenv run` and `uenv start`

The `run` command runs a single command in the configured environment, returning us to the unmodified calling shell.

This is useful to use more than one uenv in a workflow - run each step with a different uenv:

```console
uenv run --view=default prgenv-gnu -- ./pre-process.sh
uenv run --view=cp2k cp2k -- ./cp2k-simulation.sh
uenv run --view=default prgenv-gnu -- ./post-process.sh
```

Another, slightly irreverant, example is to make emacs available.
```console
which emacs
```

Emacs is provided by the `editors` uenv (access through the `ed` view):
```console
uenv run --view=ed editors:/user-tools -- emacs
```

The above command works, but is not very practical for regular use. Instead:

```console
alias emacs='uenv run --view=ed editors:/user-tools -- emacs'
emacs test.cpp
```

it seems odd, but by adding that alias to your `.bashrc`, you now have emacs available without installing any software, or modifying your environment (keep it simple).

## building software using uenv

### a simple application using prgenv-gnu

Here we build `affinity`, a small MPI+CUDA aware application for reporting CPU+GPU affinity.

A view provides all of the requirements (gcc, MPI, cuda, cmake, ninja)
```
uenv start prgenv-gnu/24.7 --view=default
git clone git@github.com:bcumming/affinity.git
cd affinity
mkdir build
cd build
which cmake
which mpicc
nvcc --version
CC=mpicc CXX=mpicxx cmake .. -GNinja
ninja

OMP_NUM_THREADS=4 srun -n4 -N1 --gpus-per-task=1 ./affinity.mpi
srun -n4 -N1 --gpus-per-task=1 ./affinity.cuda
```

The uenv provides cray-mpich, with some key differences:

* the MPI compilers are `mpicc`, `mpicxx`, `mpifort`
    * replacing the `CC`, `cc`, `ftn` compiler wrappers provided by CPE
* dependencies required for GPU-aware MPI are hard coded (no need to load specific modules)

```console
vim $(which mpicc)
```

modules are also available in most uenv:

```console
uenv start prgenv-gnu/24.7 --view=modules
module avail
module load cray-mpich cmake cuda gcc ninja

# then run cmake, ninja, as before
```

The `modules` view simply updates `MODULEPATH`:
```
{
  "list": {
    "MODULEPATH": [
      {
        "op": "prepend",
        "value": [
          "/user-environment/modules"
        ]
      }
    ]
  },
  "scalar": {}
}
```

### A more complicated example

Use a view to build Arbor, a neuroscience application that can optionally use MPI, CUDA and Python.

We use a uenv that was developed for Arbor [using a uenv recipe](https://github.com/eth-cscs/alps-uenv/blob/main/recipes/arbor/v0.9/gh200/environments.yaml).

```console
git clone --depth=1 --branch=v0.9.0 git@github.com:arbor-sim/arbor.git
mkdir build
cd build

export CC=`which gcc`
export CXX=`which g++`
cmake ../arbor -DARB_GPU=cuda -DARB_WITH_MPI=on -DARB_WITH_PYTHON=on -GNinja -DCMAKE_CUDA_ARCHITECTURES=90
ninja examples pyarb unit

# test the build
./unit
./bin/busyring
export PYTHONPATH=$PWD/python:$PYTHONPATH
python -c 'import arbor; print(arbor.config)'
```

### setting up a Python venv

Create a virtual environment that uses the software in a uenv as the starting point:
```console
uenv start arbor --view=develop

# check the version of python that is being used
which python
python --version

# create a venv
python -m venv --system-site-packages env
source env/bin/activate
pip list
```

### building using Spack

Spack is a popular tool for installing scientific software:

* configure the software to install `arbor@v0.10.0+mpi+cuda+python`
* Spack will build all missing dependencies

Each uenv image provides a standard Spack configuration

* Can be used as the basis for your own spack environment

The spack configuration can be accessed using the `spack` view:

```console
>uenv start prgenv-gnu --view=spack
loading the view prgenv-gnu:spack
> printenv | grep UENV_SPACK
UENV_SPACK_COMMIT=bd66dce2d668a6234504594661506cdd1eaca4adc
UENV_SPACK_CONFIG_PATH=/user-environment/config
UENV_SPACK_URL=https://github.com/spack/spack.git
> git clone $UENV_SPACK_URL
> cd spack
> cat /user-environment/meta/recipe/config.yaml
name: prgenv-gnu
spack:
  commit: releases/v0.22
  repo: https://github.com/spack/spack.git
store: /user-environment
description: GNU Compiler toolchain with cray-mpich, Python, CMake and other development tools.
> git switch releases/v0.22
> ./bin/spack find
> ./bin/spack -C $UENV_SPACK_CONFIG_PATH find
```

See uenv documentation for how to use the packages installed in a uenv with Spack to install your own software:

https://eth-cscs.github.io/alps-uenv/uenv-compilation-spack/

# Applications provided by uenv

So far our examples have provided examples of using common CLI tools and compilers provided by uenv to work in the terminal and build scientific software.

Uenv can also provide scientific software and tools like debuggers - no compilation necessary.

There are application uenv provided by CSCS for common scientific codes:

* CP2K
* GROMACS
* NAMD
* LAMMPS
* ICON
* VASP
* quantumespresso
* and more ...

Scientific software is diverse, so there is no hard and fast rule for which views will be provided.
```
quantumespresso : default develop modules spack
namd            : namd namd-single-node develop develop-single-node modules spack
cp2k            : cp2k develop modules spack
arbor           : arbor develop modules spack
```

Typically, the uenv provide two types of view:

* an `application view` that provides the application
    * "ready to run"
    * like `module load <application>`
    * use this to directly use the version of the software provided by CSCS
* a `development view` that provides all of the application's dependencies
    * use this to build your own version of the software
    * e.g. if you need a different version or configuration

# slurm

So far we have looked at using `uenv start` and `uenv run` to interact with uenv.
Both of these approaches load the uenv _on the node that the command is run on_.
This is an important detail - the uenv is not mounted on compute nodes, and is only visible to the current process.

We can test that:
```console
# by default, nothing mounted on the compute node
srun -n1 ls /user-environment

# start a uenv on the login node and try again
uenv start prgenv-gnu
srun -n1 ls /user-environment/
```

The image was mounted on the compute node - what is going on?

There is a uenv slurm plugin that will handle mounting uenv on compute nodes.
By default, if

* no `--uenv` flag is passed
* a uenv was mounted on the login node when srun was called

The plugin will mount the image automatically on the login node

* related: why are the modules loaded when calling sbatch on a login node loaded on all the compute nodes?

Using `uenv start` and `uenv run` inside an sbatch job script has downsides:

* it increases the complexity of the job script
* it may be inefficient in some cases
    * e.g. 128 ranks on a single node all mount the same uenv image

The uenv Slurm plugin automates the process of starting uenv

* the uenv to load is provided using a `--uenv` option
* the plugin then:
    1. validates the request on the login node (when srun or sbatch is called)
    2. mounts the uenv on each compute node before the individual MPI ranks are created
* the uenv is automatically removed when each `srun` command finishes.

From the perspective of the script running on the compute node, the uenv is always mounted.

A simple example using `srun`
```console
# start a shell on a compute node with the uenv mounted
srun -n1 --uenv=prgenv-gnu/24.7:v3 --pty bash


# run a command on a compute node with the uenv mounted
srun -n1 --uenv=prgenv-gnu/24.7:v3 bash -c 'uenv view modules; module avail'
```

## using uenv in sbatch jobs

The `--uenv` flag can also be used in slurm batch jobs:

```bash
#!/bin/bash
#SBATCH --uenv=prgenv-gnu/24.7:v3
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --output=job%j.out
#SBATCH --error=job%j.out

# load the view
uenv view default
exe=/capstor/scratch/cscs/bcumming/demo/affinity/build/affinity.cuda

# the uenv is available inside the script
which nvcc
uenv status

# and also automatically mounted on the compute nodes:
srun -n4 -N1 $exe

# note: within this week the following will be possible

#srun -n4 -N1 --uenv=prgenv-gnu --uenv-view=default affinity.gpu
```

Sometimes a job will require multiple uenv, e.g. pre-processing and post-processing stages might use one uenv, and the simulation runs would use an application uenv.
The uenv specified in the `#SBATCH --uenv=` comment can be overriden in individual calls to `srun` inside the script.
For example, run a job that first uses the affinity application that we built earlier with `prgenv-gnu`, then run an arbor benchmark that was built with the `arbor` uenv.

```bash
#!/bin/bash
#SBATCH --uenv=prgenv-gnu/24.7:v3
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --output=job%j.out
#SBATCH --error=job%j.out

# load the view
uenv view default
exe=/capstor/scratch/cscs/bcumming/demo/affinity/build/affinity.cuda

srun -n4 -N1 $exe

arbor=/capstor/scratch/cscs/bcumming/demo/arbor/build/bin/busyring
srun --uenv=arbor/v0.9 -n4 -N1 --gpus-per-task=1 $arbor
```

???+ note

    The `--uenv` slurm flag is a little awkward to use at the moment because there is no corresponding `--view` flag.
    This forces us th use `uenv view` command separately, which is messy and can create significant complexity in scripts.

    A new version of the slurm plugin will be deployed on Daint and Todi very soon - hopefully this week - that will provide the `--uenv-view` flag.
